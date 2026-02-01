/**
 * QR Code Component
 * Displays a QR code from a URL or data URI
 */

interface QRCodeProps {
  url: string // QR code image URL or data URI
  alt?: string
  size?: number
  className?: string
}

export function QRCode({ url, alt = 'QR Code', size = 200, className = '' }: QRCodeProps) {
  return (
    <div className={`inline-block ${className}`}>
      <img
        src={url}
        alt={alt}
        width={size}
        height={size}
        className="border-[0.5px] border-safe/30 rounded-none"
      />
    </div>
  )
}
