import { useEffect, useState } from 'react'

function App() {
  const [status, setStatus] = useState('正在检查 Backend...')

  useEffect(() => {
    fetch('/api/health')
      .then((response) => response.json())
      .then((data: { status: string }) => setStatus(`Backend 状态：${data.status}`))
      .catch(() => setStatus('Backend 尚未连接'))
  }, [])

  return (
    <main style={{ fontFamily: 'sans-serif', maxWidth: 760, margin: '80px auto', padding: 24 }}>
      <h1>Rental App</h1>
      <p>水上器材租赁管理系统</p>
      <p>{status}</p>
      <p>当前是最小项目骨架，业务功能尚未实现。</p>
    </main>
  )
}

export default App
