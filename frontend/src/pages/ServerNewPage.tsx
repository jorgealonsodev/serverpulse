import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useState } from 'react'
import { Plus } from 'lucide-react'
import Layout from '@/components/Layout'
import CopyButton from '@/components/CopyButton'
import * as serversApi from '@/api/servers'
import type { ServerWithToken } from '@/types'

const serverSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  hostname: z.string().optional(),
})

type ServerFormData = z.infer<typeof serverSchema>

export default function ServerNewPage() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ServerFormData>({
    resolver: zodResolver(serverSchema),
  })

  const [created, setCreated] = useState<ServerWithToken | null>(null)
  const [error, setError] = useState<string | null>(null)

  const onSubmit = async (data: ServerFormData) => {
    setError(null)
    try {
      const server = await serversApi.create(data.name, data.hostname ?? '')
      setCreated(server)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create server')
    }
  }

  if (created) {
    const installCmd = `curl -sSL https://serverpulse.example.com/install.sh | bash -s -- --token ${created.api_token} --hostname ${created.hostname ?? 'localhost'}`

    return (
      <Layout>
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold mb-6">Server Created</h2>

          <div className="bg-card border border-border rounded-lg p-6 mb-6">
            <h3 className="text-lg font-medium mb-2">{created.name}</h3>
            <p className="text-sm text-gray-400 mb-4">
              Save this token now — it will only be shown once.
            </p>

            <div className="flex items-center gap-2 mb-4">
              <code className="flex-1 px-3 py-2 bg-bg border border-border rounded-lg text-sm font-mono break-all">
                {created.api_token}
              </code>
              <CopyButton text={created.api_token} />
            </div>

            <h4 className="text-sm font-medium text-gray-300 mb-2">Install command</h4>
            <div className="flex items-start gap-2">
              <pre className="flex-1 px-3 py-2 bg-bg border border-border rounded-lg text-sm font-mono whitespace-pre-wrap break-all">
                {installCmd}
              </pre>
              <CopyButton text={installCmd} />
            </div>
          </div>

          <div className="flex gap-3">
            <a
              href="/"
              className="px-4 py-2 bg-accent text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              Go to Dashboard
            </a>
            <button
              onClick={() => setCreated(null)}
              className="px-4 py-2 bg-border text-gray-300 rounded-lg hover:bg-gray-600 transition-colors"
            >
              Add Another
            </button>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="max-w-md mx-auto">
        <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <Plus className="w-6 h-6" />
          Add Server
        </h2>

        {error && (
          <div className="mb-4 p-3 bg-danger/10 border border-danger/30 text-danger text-sm rounded-lg">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-1">
              Server Name
            </label>
            <input
              id="name"
              {...register('name')}
              className="w-full px-3 py-2 bg-bg border border-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent"
              placeholder="production-web-01"
              autoFocus
            />
            {errors.name && (
              <p className="mt-1 text-sm text-danger">{errors.name.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="hostname" className="block text-sm font-medium text-gray-300 mb-1">
              Hostname (optional)
            </label>
            <input
              id="hostname"
              {...register('hostname')}
              className="w-full px-3 py-2 bg-bg border border-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent"
              placeholder="web01.example.com"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-2 bg-accent text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
          >
            {isSubmitting ? 'Creating...' : 'Create Server'}
          </button>
        </form>
      </div>
    </Layout>
  )
}
