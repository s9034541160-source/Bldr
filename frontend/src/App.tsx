import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from 'antd'
import MainLayout from './layout/MainLayout'
import HomePage from './pages/HomePage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<HomePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

