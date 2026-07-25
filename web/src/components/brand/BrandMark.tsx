import logo from '@/assets/kahani-studio.png'
import { cn } from '@/lib/utils'

type BrandMarkProps = {
  size?: number
  className?: string
}

/** Kahani Studio logo mark. */
export function BrandMark({ size = 32, className }: BrandMarkProps) {
  return (
    <img
      src={logo}
      alt="Kahani Studio"
      width={size}
      height={size}
      draggable={false}
      className={cn('shrink-0 rounded-[8px] object-cover', className)}
      style={{ width: size, height: size }}
    />
  )
}
