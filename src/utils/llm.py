import os

import anthropic
import bs4
import openai

class Vendor:
    pass

class Anthropic(Vendor):

    def __init__(self, api_key: str = None, default_model_name: str = 'claude-3-5-haiku-20241022'):
        self.default_model_name = default_model_name
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            self.client = anthropic.Anthropic()


    def complete(self, messages: list[dict], max_tokens=1000, temperature=0, model_name=None):
        if model_name is None:
            model_name = self.default_model_name

        system_prompt = ""
        _messages = []

        for message in messages:
            if message["role"] == "system":
                system_prompt = system_prompt + message["content"]
            else:
                _messages.append(message)


        result=self.client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=_messages
        )
        return result.content[0].text

class OpenAI(Vendor):

    def __init__(self, api_key: str = None, default_model_name: str = "gpt-4o-mini"):
        self.default_model_name = default_model_name
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])


    def complete(self, messages: list[dict], max_tokens=1000, temperature=0, model_name=None):

        if model_name is None:
            model_name = self.default_model_name

        completion = self.client.chat.completions.create(
            model=model_name, 
            max_completion_tokens=max_tokens,
            messages=messages,
            temperature=temperature
        )

        return completion.choices[0].message.content
    
    def complete_structured(self, messages: list[dict], response_format, max_tokens=1000, temperature=0, model_name=None):
        if model_name is None:
            model_name = self.default_model_name

        completion = self.client.beta.chat.completions.parse(
            model=model_name, 
            messages=messages,
            response_format=response_format,
        )

        return completion.choices[0].message.parsed

def split_prompt_to_messages(rendered_prompt):
    messages = []
    rendered_prompt.replace("<text>", "<text><![CDATA[")
    rendered_prompt.replace("</text>", "]]<\text>")
    soup = bs4.BeautifulSoup(rendered_prompt, "html.parser")
    message_tags = soup.find_all("message")
    for mtag in message_tags:
        role = mtag.attrs["role"]
        for tag in mtag.find_all():
            messages.append({
                "role": role,
                "content": tag.text.strip()
            })
    return messages
        