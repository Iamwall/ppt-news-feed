import clsx from 'clsx'
import { Loader2, CheckCircle, XCircle, Clock, FileText } from 'lucide-react'
import { DigestStatus } from '../types'

interface StatusBadgeProps {
  status: DigestStatus
  size?: 'sm' | 'md'
}

export default function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const config = {
    created: {
      icon: FileText,
      label: 'Created',
      className: 'badge-neutral',
      animate: false,
    },
    pending: {
      icon: Clock,
      label: 'Pending',
      className: 'badge-neutral',
      animate: false,
    },
    processing: {
      icon: Loader2,
      label: 'Processing',
      className: 'badge-warning',
      animate: true,
    },
    // @ts-ignore - running might not be in DigestStatus but kept for safety
    running: { 
      icon: Loader2,
      label: 'Running',
      className: 'badge-warning',
      animate: true,
    },
    completed: {
      icon: CheckCircle,
      label: 'Completed',
      className: 'badge-success',
      animate: false,
    },
    failed: {
      icon: XCircle,
      label: 'Failed',
      className: 'badge-danger',
      animate: false,
    },
  }
  
  // @ts-ignore - indexing with explicit DigestStatus might fail if we access 'running' which is not in keyof
  const { icon: Icon, label, className, animate } = config[status] || config.pending
  
  return (
    <span className={clsx(
      className,
      size === 'sm' && 'text-xs px-2 py-0.5',
      size === 'md' && 'text-sm px-2.5 py-1'
    )}>
      <Icon className={clsx(
        'mr-1.5',
        size === 'sm' && 'w-3 h-3',
        size === 'md' && 'w-4 h-4',
        animate && 'animate-spin'
      )} />
      {label}
    </span>
  )
}
