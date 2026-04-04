import React from 'react'

type Props = { children: React.ReactNode }
type State = { hasError: boolean }

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error: any, info: any) {
    // In production, send to monitoring
    console.error('ErrorBoundary caught', error, info)
  }

  render() {
    if (this.state.hasError) {
      return <div style={{ padding: 20, color: '#fff' }}>出现错误，请刷新页面或联系管理员。</div>
    }
    return this.props.children
  }
}

export default ErrorBoundary
