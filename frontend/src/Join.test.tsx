import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Join } from './Join';

function renderJoin(overrides: Partial<React.ComponentProps<typeof Join>> = {}) {
  const props = {
    room: 'demo',
    name: 'Alice',
    setRoom: vi.fn(),
    setName: vi.fn(),
    onJoin: vi.fn(),
    busy: false,
    error: null,
    ...overrides,
  };
  render(<Join {...props} />);
  return props;
}

describe('Join — happy path', () => {
  it('renders the Customer Onboarding heading', () => {
    renderJoin();
    expect(screen.getByRole('heading', { name: 'Customer Onboarding' })).toBeInTheDocument();
  });

  it('button is disabled when name is empty', () => {
    renderJoin({ name: '' });
    expect(screen.getByRole('button', { name: /start onboarding/i })).toBeDisabled();
  });

  it('button is disabled when room is empty', () => {
    renderJoin({ room: '' });
    expect(screen.getByRole('button', { name: /start onboarding/i })).toBeDisabled();
  });

  it('button is enabled when both room and name are filled', () => {
    renderJoin({ room: 'demo', name: 'Alice' });
    expect(screen.getByRole('button', { name: /start onboarding/i })).toBeEnabled();
  });

  it('clicking the button calls onJoin', async () => {
    const { onJoin } = renderJoin();
    await userEvent.click(screen.getByRole('button', { name: /start onboarding/i }));
    expect(onJoin).toHaveBeenCalledOnce();
  });
});
