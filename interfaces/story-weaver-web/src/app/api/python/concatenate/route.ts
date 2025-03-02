import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';

export async function POST(req: NextRequest) {
  try {
    const { string1, string2 } = await req.json();
    
    // Create a Python process with error handling
    const pythonProcess = spawn('python', ['-c', `
import sys
try:
    print("${string1} ${string2}")
except Exception as e:
    print(f"Error: {str(e)}", file=sys.stderr)
`]);

    // Handle errors
    let error = '';
    for await (const chunk of pythonProcess.stderr) {
      error += chunk;
    }

    if (error) {
      return NextResponse.json({ error }, { status: 500 });
    }

    // Get the output
    let result = '';
    for await (const chunk of pythonProcess.stdout) {
      result += chunk;
    }

    return NextResponse.json({ result: result.trim() });
  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
} 