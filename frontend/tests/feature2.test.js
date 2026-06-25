import React from 'react';
import { render, screen } from '@testing-library/react';
import ResearchGapHistoryPage from '../src/app/feature2/page';
import { AuthContext } from '../src/contexts/AuthContext';
import { listUserTasks } from '../src/apis/researchGap';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      prefetch: () => null,
      replace: jest.fn(),
      push: jest.fn(),
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
jest.mock('../src/apis/researchGap', () => ({
  listUserTasks: jest.fn().mockResolvedValue({ status: 'success', data: [] }),
  bulkDeleteTasks: jest.fn(),
}));

describe('Feature2 (Research Gap History Page)', () => {
  const authContextValue = {
    accessToken: 'valid-token',
  };

  it('renders loading spinner initially', () => {
    listUserTasks.mockImplementation(() => new Promise(() => {})); // Never resolves
    render(
      <AuthContext.Provider value={authContextValue}>
        <ResearchGapHistoryPage />
      </AuthContext.Provider>
    );

    expect(screen.getByText('분석 이력 데이터를 불러오는 중...')).toBeInTheDocument();
  });
});
