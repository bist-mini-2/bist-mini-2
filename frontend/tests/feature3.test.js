import React from 'react';
import { render, screen } from '@testing-library/react';
import Feature3Page from '../src/app/feature3/page';
import { getGems } from '../src/apis/gemsApi';

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
jest.mock('../src/apis/gemsApi', () => ({
  getGems: jest.fn().mockResolvedValue([]),
  createGem: jest.fn(),
  updateGem: jest.fn(),
  deleteGem: jest.fn(),
}));

describe('Feature3 (Gem Manager Page)', () => {
  it('renders Gem store correctly', async () => {
    render(<Feature3Page />);

    expect(screen.getByText('Gems')).toBeInTheDocument();
    expect(screen.getByText('새 Gem 만들기')).toBeInTheDocument();
  });
});
