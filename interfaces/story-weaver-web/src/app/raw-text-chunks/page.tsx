'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

interface RawTextChunk {
  id: number
  timestamp: string
  filename: string
  speaker: string
  content: string
  created_at: string
}

export default function RawTextChunks() {
  const [chunks, setChunks] = useState<RawTextChunk[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchChunks() {
      try {
        const { data, error } = await supabase
          .from('raw_text_chunk')
          .select('*')
          .order('created_at', { ascending: false })

        if (error) throw error

        setChunks(data || [])
      } catch (e) {
        setError(e instanceof Error ? e.message : 'An error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchChunks()
  }, [])

  if (loading) return <div className="p-8">Loading...</div>
  if (error) return <div className="p-8 text-red-500">Error: {error}</div>

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Raw Text Chunks</h1>
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse border border-gray-300">
          <thead>
            <tr className="bg-gray-100">
              <th className="border border-gray-300 p-2">ID</th>
              <th className="border border-gray-300 p-2">Timestamp</th>
              <th className="border border-gray-300 p-2">Filename</th>
              <th className="border border-gray-300 p-2">Speaker</th>
              <th className="border border-gray-300 p-2">Content</th>
              <th className="border border-gray-300 p-2">Created At</th>
            </tr>
          </thead>
          <tbody>
            {chunks.map((chunk) => (
              <tr key={chunk.id} className="hover:bg-gray-50">
                <td className="border border-gray-300 p-2">{chunk.id}</td>
                <td className="border border-gray-300 p-2">{chunk.timestamp}</td>
                <td className="border border-gray-300 p-2">{chunk.filename}</td>
                <td className="border border-gray-300 p-2">{chunk.speaker}</td>
                <td className="border border-gray-300 p-2 max-w-md truncate">
                  {chunk.content}
                </td>
                <td className="border border-gray-300 p-2">
                  {new Date(chunk.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
} 