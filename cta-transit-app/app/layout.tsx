import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'CTA Transit Map - Chicago',
  description: 'Interactive map of Chicago Transit Authority bus routes and stops',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}