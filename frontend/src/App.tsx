import { Route, Routes } from "react-router-dom"
import { AppShell } from "./components/AppShell"
import { GuestOnly, RequireAuth } from "./components/Guards"
import { About } from "./pages/About"
import { Account } from "./pages/Account"
import { Anchors } from "./pages/Anchors"
import { Dashboard } from "./pages/Dashboard"
import { GameDetail } from "./pages/GameDetail"
import { Hardware } from "./pages/Hardware"
import { Landing } from "./pages/Landing"
import { Login } from "./pages/Login"
import { NotFound } from "./pages/NotFound"
import { Preferences } from "./pages/Preferences"
import { Recommendations } from "./pages/Recommendations"
import { Recover } from "./pages/Recover"
import { Register } from "./pages/Register"

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route
        path="/entrar"
        element={
          <GuestOnly>
            <Login />
          </GuestOnly>
        }
      />
      <Route
        path="/cadastro"
        element={
          <GuestOnly>
            <Register />
          </GuestOnly>
        }
      />
      <Route
        path="/recuperar"
        element={
          <GuestOnly>
            <Recover />
          </GuestOnly>
        }
      />
      <Route
        path="/app"
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="preferencias" element={<Preferences />} />
        <Route path="ancoras" element={<Anchors />} />
        <Route path="hardware" element={<Hardware />} />
        <Route path="recomendacoes" element={<Recommendations />} />
        <Route path="jogos/:id" element={<GameDetail />} />
        <Route path="conta" element={<Account />} />
        <Route path="sobre" element={<About />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
