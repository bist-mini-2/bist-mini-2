import React from 'react';
import { render, screen } from '@testing-library/react';
import Feature4Page from '../src/app/feature4/arena/page';

// Mock react-markdown
jest.mock('react-markdown', () => {
  return ({ children }) => <>{children}</>;
});

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

// Mock Link
jest.mock('next/link', () => {
  return ({ children, href }) => {
    return <a href={href}>{children}</a>;
  };
});

// Mock apis
jest.mock('../src/apis/defenseArena', () => ({
  uploadIsolatedPdf: jest.fn(),
  runAcademicPeerReview: jest.fn(),
  verifyHypothesis: jest.fn(),
  defenseChatArena: jest.fn(),
}));

describe('Feature4 (Defense Arena Page)', () => {
  it('renders upload sandbox when sessionId is null', () => {
    render(<Feature4Page />);

    expect(screen.getByText(/분석할 PDF.*클릭 업로드/)).toBeInTheDocument();
  });
});
