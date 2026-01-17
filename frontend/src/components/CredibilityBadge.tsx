import clsx from 'clsx'
import { Shield, ShieldCheck, ShieldAlert, ShieldQuestion } from 'lucide-react'

interface CredibilityBadgeProps {
  score: number | null
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

export default function CredibilityBadge({ 
  score, 
  size = 'md',
  showLabel = true 
}: CredibilityBadgeProps) {
  if (score === null) {
    return (
      <span className={clsx(
        'badge-neutral flex items-center gap-1',
        size === 'sm' && 'text-xs px-2 py-0.5',
        size === 'md' && 'text-sm px-2.5 py-1',
        size === 'lg' && 'text-base px-3 py-1.5'
      )}>
        <ShieldQuestion className={clsx(
          size === 'sm' && 'w-3 h-3',
          size === 'md' && 'w-4 h-4',
          size === 'lg' && 'w-5 h-5'
        )} />
        {showLabel && <span>Not Assessed</span>}
      </span>
    )
  }
  
  const roundedScore = Math.round(score)
  
  let variant: 'success' | 'warning' | 'danger'
  let Icon: typeof Shield

  
  if (roundedScore >= 70) {
    variant = 'success'
    Icon = ShieldCheck

  } else if (roundedScore >= 50) {
    variant = 'warning'
    Icon = Shield

  } else {
    variant = 'danger'
    Icon = ShieldAlert

  }
  
  return (
    <span className={clsx(
      'flex items-center gap-1.5',
      variant === 'success' && 'badge-success',
      variant === 'warning' && 'badge-warning',
      variant === 'danger' && 'badge-danger',
      size === 'sm' && 'text-xs px-2 py-0.5',
      size === 'md' && 'text-sm px-2.5 py-1',
      size === 'lg' && 'text-base px-3 py-1.5'
    )}>
      <Icon className={clsx(
        size === 'sm' && 'w-3 h-3',
        size === 'md' && 'w-4 h-4',
        size === 'lg' && 'w-5 h-5'
      )} />
      <span className="font-semibold">{roundedScore}</span>
      {showLabel && <span className="opacity-75">/ 100</span>}
    </span>
  )
}
