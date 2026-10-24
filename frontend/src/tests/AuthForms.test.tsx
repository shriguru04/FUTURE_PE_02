import type { ReactNode } from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { LoginPage, RegisterPage } from '../pages/AuthPages'

const login = vi.fn()
const signup = vi.fn()
vi.mock('../context/AuthContext', () => ({ useAuth: () => ({ login, register: signup }) }))
vi.mock('../context/ToastContext', () => ({ useToast: () => ({ success: vi.fn(), error: vi.fn() }) }))

const wrap = (ui: ReactNode) => render(<MemoryRouter>{ui}</MemoryRouter>)

describe('auth form validation', () => {
  beforeEach(() => { login.mockReset(); signup.mockReset() })

  it('login blocks empty submit and shows errors', async () => {
    wrap(<LoginPage />)
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))
    expect(await screen.findByText('Email is required.')).toBeInTheDocument()
    expect(screen.getByText('Password is required.')).toBeInTheDocument()
    expect(login).not.toHaveBeenCalled()
  })

  it('login rejects malformed email', async () => {
    wrap(<LoginPage />)
    await userEvent.type(screen.getByLabelText('Email'), 'not-an-email')
    await userEvent.type(screen.getByLabelText('Password'), 'whatever')
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))
    expect(await screen.findByText('Enter a valid email address.')).toBeInTheDocument()
  })

  it('register enforces minimum password length', async () => {
    wrap(<RegisterPage />)
    await userEvent.type(screen.getByLabelText('Email'), 'a@b.co')
    await userEvent.type(screen.getByLabelText('Password'), 'short')
    await userEvent.click(screen.getByRole('button', { name: /create account/i }))
    expect(await screen.findByText('Use at least 8 characters.')).toBeInTheDocument()
    expect(signup).not.toHaveBeenCalled()
  })

  it('login submits valid credentials', async () => {
    login.mockResolvedValue(undefined)
    wrap(<LoginPage />)
    await userEvent.type(screen.getByLabelText('Email'), 'a@b.co')
    await userEvent.type(screen.getByLabelText('Password'), 'secret-pass')
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))
    await waitFor(() => expect(login).toHaveBeenCalledWith('a@b.co', 'secret-pass'))
  })
})
