import streamlit as st
import difflib
import re
from typing import Iterator, Tuple

from src.utils.llm import Anthropic, OpenAI

COMMON_WORDS = {"a", "an", "the", "to", "of", "for", "it", "and", "or", "if", "is", 
                "be", "am", "are", "as", "do", "did", "done", "like", "that", "this"}


vendor_name = st.selectbox("Select a vendor", ["openai", "anthropic"])
model_name = st.text_input("(Optional) Enter a model name", "default")
if vendor_name == "anthropic":
    anthropic_api_key = st.text_input("Enter an Anthropic API key: ", "Your key here")
    if model_name != "default":
        vendor = Anthropic(api_key=anthropic_api_key, default_model_name=model_name)
    else:
        vendor = Anthropic(api_key=anthropic_api_key)
else:
    openai_api_key = st.text_input("Enter an OpenAI API Key:", "Your key here")
    if model_name != "default":
        vendor = OpenAI(api_key=openai_api_key, default_model_name=model_name)
    else:
        vendor = OpenAI(api_key=openai_api_key)


def parse_timestamp_sections(text: str) -> Iterator[Tuple[str, str, str]]:
    """
    Parse text into sections based on timestamps.
    Yields tuples of (timestamp, speaker, content)
    """
    # Pattern matches both MM:SS and HH:MM:SS formats
    timestamp_pattern = (
        r'^(\d{2}:\d{2}(?::\d{2})?)\n([^\n]+)\n([^\n](?:.*?)(?=\n\d{2}:\d{2}(?::\d{2})?\n|$))'
    )

    matches = re.finditer(timestamp_pattern, text, re.MULTILINE | re.DOTALL)
    for match in matches:
        timestamp = match.group(1)
        speaker = match.group(2)
        content = match.group(3).strip()
        yield timestamp, speaker, content

def process_with_llm(texts, system_prompt):
    """
    Get corrected text from LLM.
    In your real code, you'd call vendor.complete() or similar here.
    """
    messages = [
        {"role": "system", "content": system_prompt},
    ] + texts
    try:
        response = vendor.complete(messages=messages)
        if len(response.replace("None", "")) < 3:
            return ""
        return response
    except Exception as e:
        st.error(f"Error processing text: {str(e)}")
        return ""

def tokenize(text):
    """
    Splits text into tokens (words + punctuation).
    Example: "I said, hello." -> ["I", "said", ",", "hello", "."]
    """
    return re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE)

def are_similar_words(word1, word2, threshold=0.7):
    """
    Returns True if word1 and word2 are similar enough to be considered a 'revision'.
    Uses difflib.SequenceMatcher ratio.
    """
    w1, w2 = word1.lower(), word2.lower()
    # If either word is too short (<=2 chars), require exact match
    if len(w1) <= 2 or len(w2) <= 2:
        return (w1 == w2)
    ratio = difflib.SequenceMatcher(None, w1, w2).ratio()
    return (ratio >= threshold)

def force_reclassify_small_equals(opcodes, orig_tokens, corr_tokens):
    """
    Second-pass cleanup:
    - If we see an 'equal' chunk that consists solely of short/common words
      sandwiched between large replaced chunks, reclassify it as replaced.
    - This helps avoid random small words ('a', 'the', 'to', etc.) from anchoring
      as 'equal' in the middle of a big rewrite.
    Returns a new list of opcodes with these small 'equal' blocks merged into neighboring replaces.
    """
    new_opcodes = []
    n = len(opcodes)
    i = 0

    while i < n:
        op, start1, end1, start2, end2 = opcodes[i]

        if op == "equal":
            # Extract the tokens in this equal chunk
            eq_orig = orig_tokens[start1:end1]
            eq_corr = corr_tokens[start2:end2]
            length_orig = (end1 - start1)
            length_corr = (end2 - start2)

            # Heuristic: if the chunk is short AND the tokens are all in COMMON_WORDS or are very short,
            # we *might* want to force it into a 'replace' if it's sandwiched by big diffs.
            chunk_is_small = (length_orig <= 2 and length_corr <= 2)
            all_common = all(
                (t.lower() in COMMON_WORDS or len(t) <= 3) 
                for t in eq_orig + eq_corr
            )

            # Check neighbors: if both neighbors are large replaces, we reclassify.
            if chunk_is_small and all_common:
                # Look at prev and next if they exist
                prev_is_replace = (i > 0 and opcodes[i-1][0] in ["replace", "delete", "insert"])
                next_is_replace = (i < n-1 and opcodes[i+1][0] in ["replace", "delete", "insert"])

                if prev_is_replace or next_is_replace:
                    # Reclassify this entire "equal" chunk as replaced
                    new_opcodes.append(("replace", start1, end1, start2, end2))
                    i += 1
                    continue

            # If we didn't reclassify, keep it as-is.
            new_opcodes.append((op, start1, end1, start2, end2))
            i += 1

        else:
            # For replace/insert/delete, just add them
            new_opcodes.append((op, start1, end1, start2, end2))
            i += 1

    return new_opcodes

def diff_tokens(orig_tokens, corr_tokens, similarity_threshold=0.7):
    """
    Produces two parallel lists of tokens with <DEL>, <ADD>, <REV>, or unmarked “equal” tokens.
    """
    # First-pass: basic difflib alignment
    matcher = difflib.SequenceMatcher(None, orig_tokens, corr_tokens)
    opcodes = matcher.get_opcodes()

    # Second-pass: reclassify small 'equal' chunks that are likely spurious
    opcodes = force_reclassify_small_equals(opcodes, orig_tokens, corr_tokens)

    # Build final tagged tokens
    orig_tagged = []
    corr_tagged = []

    for op, i1, i2, j1, j2 in opcodes:
        if op == "equal":
            # Exactly the same, so no tags
            orig_tagged.extend(orig_tokens[i1:i2])
            corr_tagged.extend(corr_tokens[j1:j2])

        elif op == "delete":
            for w in orig_tokens[i1:i2]:
                orig_tagged.append(f"<DEL>{w}</DEL>")

        elif op == "insert":
            for w in corr_tokens[j1:j2]:
                corr_tagged.append(f"<ADD>{w}</ADD>")

        elif op == "replace":
            sub_orig = orig_tokens[i1:i2]
            sub_corr = corr_tokens[j1:j2]
            # If lengths match, try to do a finer pairing
            if len(sub_orig) == len(sub_corr):
                for w1, w2 in zip(sub_orig, sub_corr):
                    if are_similar_words(w1, w2, similarity_threshold):
                        orig_tagged.append(f"<REV>{w1}</REV>")
                        corr_tagged.append(f"<REV>{w2}</REV>")
                    else:
                        orig_tagged.append(f"<DEL>{w1}</DEL>")
                        corr_tagged.append(f"<ADD>{w2}</ADD>")
            else:
                # Different lengths => each side is fully replaced
                for w1 in sub_orig:
                    orig_tagged.append(f"<DEL>{w1}</DEL>")
                for w2 in sub_corr:
                    corr_tagged.append(f"<ADD>{w2}</ADD>")

    return orig_tagged, corr_tagged

def find_differences(original_text, corrected_text, similarity_threshold=0.7):
    """
    High-level function:
    1) Tokenizes the original and corrected texts.
    2) Produces parallel lists of tokens with <DEL>, <ADD>, <REV>, or no tag (equal).
    """
    orig_tokens = tokenize(original_text)
    corr_tokens = tokenize(corrected_text)
    return diff_tokens(orig_tokens, corr_tokens, similarity_threshold)

def highlight_original_text(tagged_original_tokens):
    """
    Convert tokens with <DEL> or <REV> tags into styled HTML for the original side.
      - <DEL> => red
      - <REV> => orange highlight
      - untagged => normal text
    """
    output = []
    for tok in tagged_original_tokens:
        if tok.startswith("<DEL>") and tok.endswith("</DEL>"):
            word = tok[5:-6]  # strip <DEL> and </DEL>
            output.append(f"<span style='color:red;'>{word}</span>")
        elif tok.startswith("<REV>") and tok.endswith("</REV>"):
            word = tok[5:-6]
            output.append(f"<span style='color:orange;'>{word}</span>")
        else:
            # Equal token (or punctuation)
            output.append(tok)
    return " ".join(output)

def highlight_corrected_text(tagged_corrected_tokens):
    """
    Convert tokens with <ADD> or <REV> tags into styled HTML for the corrected side.
      - <ADD> => green
      - <REV> => orange highlight
      - untagged => normal text
    """
    output = []
    for tok in tagged_corrected_tokens:
        if tok.startswith("<ADD>") and tok.endswith("</ADD>"):
            word = tok[5:-6]  # strip <ADD> and </ADD>
            output.append(f"<span style='color:green;'>{word}</span>")
        elif tok.startswith("<REV>") and tok.endswith("</REV>"):
            word = tok[5:-6]
            output.append(f"<span style='color:orange;'>{word}</span>")
        else:
            output.append(tok)
    return " ".join(output)

def stream_sections(transcript_text, system_prompt):
    """
    Generator that processes each transcript section in a streaming fashion.
    For each section, display side-by-side color-coded original and corrected text.
    """
    sections = list(parse_timestamp_sections(transcript_text))

    for idx, (timestamp, speaker, content) in enumerate(sections):
        # Process content with LLM
        cleaned_content = process_with_llm(
            texts=[{"role": "user", "content": content}],
            system_prompt=system_prompt
        )

        orig_tagged, corr_tagged = find_differences(content, cleaned_content)

        original_highlighted = highlight_original_text(orig_tagged)
        corrected_highlighted = highlight_corrected_text(corr_tagged)

        st.session_state.processed_sections.append(
            {
                "timestamp": timestamp,
                "speaker": speaker,
                "original_content": content,
                "cleaned_content": cleaned_content,
            }
        )

        with st.container():
            st.markdown(f"### {timestamp} — {speaker}")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Original Text**")
                st.markdown(original_highlighted, unsafe_allow_html=True)

            with col2:
                st.markdown("**Corrected Text**")
                st.markdown(corrected_highlighted, unsafe_allow_html=True)

            with col3:
                edited_text = st.text_area(
                    label=f"Editable: {timestamp} - {speaker}",
                    value=cleaned_content,
                    height=max(2, len(cleaned_content) // 30 + 1) * 34,
                    key=f"text_area_{idx}",  # unique key
                )
                st.session_state.processed_sections[idx]["cleaned_content"] = edited_text

        st.divider()

    yield "All sections processed!"


def main():
    st.title("Transcript Cleaner")

    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = (
            """Clean up the given transcription text. Fix grammar, remove filler words, fix obvious transcription errors, and make the text more readable while preserving the core meaning and as much detail and original wording as possible. Keep it conversational but clear. If the segment provided seems to be from an interviewer, return None and nothing else. If the segment does not contain any useful information for story-telling purposes, return None and nothing else. If you cannot generate an output, return None and nothing else. 

You may augment the given segment using context from previous segments. You may summarize previous segments if they have not yet been summarized. However, you cannot reprocess information you have already processed.

Example input: "Okay um so like I was thinking maybe we could..."
Example output: "I was thinking we could..."
"""
        )

    if "input_text" not in st.session_state:
        st.session_state.input_text = ""

    if "processed_sections" not in st.session_state:
        # Each item in processed_sections: {
        #   "timestamp": str,
        #   "speaker": str,
        #   "original_content": str,
        #   "cleaned_content": str
        # }
        st.session_state.processed_sections = []

    if "concatenated_text" not in st.session_state:
        st.session_state.concatenated_text = ""

    st.session_state.system_prompt = st.text_area(
        "System prompt for cleaning transcript:",
        value=st.session_state.system_prompt,
        height=150,
    )

    st.session_state.input_text = st.text_area(
        "Paste transcript here:", value=st.session_state.input_text, height=400
    )

    if st.button("Process Transcript"):
        st.session_state.processed_sections.clear()
        st.write_stream(stream_sections(st.session_state.input_text, st.session_state.system_prompt))


    if st.button("Save Combined Text"):
        concatenated = []
        for section in st.session_state.processed_sections:
            timestamp = section["timestamp"]
            speaker = section["speaker"]
            content = section["cleaned_content"]
            if content.strip():
                concatenated.append(f"=== {timestamp} - {speaker} ===\n{content}\n")

        final_text = "\n".join(concatenated)
        st.session_state.concatenated_text = final_text

        st.success("Successfully created concatenated text!")
        with st.expander("Preview saved content"):
            st.text(st.session_state.concatenated_text)

        st.download_button(
            label="Download .txt file",
            data=st.session_state.concatenated_text,
            file_name="concatenated_text.txt",
            mime="text/plain",
        )


if __name__ == "__main__":
    main()
