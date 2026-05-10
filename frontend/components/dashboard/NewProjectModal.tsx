'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { createProject } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'

const PLATFORMS = [
  { value: 'douyin', label: 'Douyin', ratio: '9:16' },
  { value: 'xiaohongshu', label: 'Xiaohongshu', ratio: '9:16' },
  { value: 'taobao', label: 'Taobao', ratio: '1:1' },
  { value: 'bilibili', label: 'Bilibili', ratio: '16:9' },
  { value: 'custom', label: 'Custom', ratio: '16:9' },
] as const

interface NewProjectModalProps {
  open: boolean
  onClose: () => void
}

export function NewProjectModal({ open, onClose }: NewProjectModalProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [platform, setPlatform] = useState<string>('douyin')
  const queryClient = useQueryClient()

  const createMutation = useMutation({
    mutationFn: () => createProject({ name: name || 'Untitled Project', description: description || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setName('')
      setDescription('')
      onClose()
    },
  })

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="New Project"
      footer={
        <>
          <Button variant="ghost" size="sm" onClick={onClose}>Cancel</Button>
          <Button
            variant="primary"
            size="sm"
            icon={<Plus className="size-3.5" />}
            onClick={() => createMutation.mutate()}
            disabled={!name.trim() || createMutation.isPending}
          >
            {createMutation.isPending ? 'Creating...' : 'Create Project'}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <Input
          label="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="My video project"
        />

        <div className="flex flex-col gap-1.5">
          <label className="label-caps text-[var(--muted-dim)]">Description</label>
          <textarea
            className="h-8 rounded-[5px] border border-[var(--outline-variant)] bg-[var(--surface-lowest)] px-3 py-2 text-[13px] text-[var(--on-surface)] outline-none transition-all duration-150 placeholder:text-[var(--muted-dim)] focus:border-[var(--accent)] focus:shadow-[inset_0_1px_2px_rgba(0,0,0,0.2),0_0_0_2px_rgba(107,92,255,0.15)]"
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What kind of video do you want to create?"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="label-caps text-[var(--muted-dim)]">Target Platform</label>
          <div className="flex flex-wrap gap-1.5">
            {PLATFORMS.map((p) => (
              <button
                key={p.value}
                className={`rounded-[4px] border px-2.5 py-1.5 text-[11px] font-medium transition-all duration-150 active:scale-[0.97] ${
                  platform === p.value
                    ? 'border-[var(--accent)]/50 bg-[var(--accent)]/10 text-[var(--accent)] shadow-[0_0_0_1px_rgba(107,92,255,0.15)]'
                    : 'border-[var(--outline-variant)]/50 text-[var(--muted)] hover:border-[var(--accent)]/30 hover:text-[var(--on-surface)]'
                }`}
                onClick={() => setPlatform(p.value)}
              >
                {p.label} <span className="text-[var(--muted)]/70">{p.ratio}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </Modal>
  )
}