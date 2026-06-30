import React from 'react';
import { render, screen } from '@testing-library/react';
import Feature1Page from '../src/app/feature1/page';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      prefetch: () => null,
      replace: jest.fn(),
      push: jest.fn(),
    };
  },
  useSearchParams() {
    return {
      get: jest.fn().mockReturnValue(null),
    };
  },
}));

// Mock react-markdown
jest.mock('react-markdown', () => {
  return ({ children }) => {
    return <div>{children}</div>;
  };
});

// Mock bioChatApi
jest.mock('../src/apis/bioChatApi', () => ({
  getMessages: jest.fn().mockResolvedValue({ data: [] }),
  createSession: jest.fn(),
  sendMessage: jest.fn(),
  sendMessageStream: jest.fn(),
  generateTitle: jest.fn(),
}));

describe('Feature1Page (RAG Chat Hub)', () => {
  it('renders Clover empty state correctly when sessionId is not provided', () => {
    render(<Feature1Page />);

    expect(screen.getByText('논문 에이전트')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/생명공학·천문학·컴퓨터공학 논문/)).toBeInTheDocument();
  });
});
