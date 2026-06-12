import { render, screen } from '@testing-library/react';
import Feature1Page from '@/app/feature1/page';
import { AuthContext } from '@/contexts/AuthContext';

describe('Feature1Page', () => {
  it('renders page1 text and user name correctly', () => {
    render(
      <AuthContext.Provider value={{ user: 'TestUser' }}>
        <Feature1Page />
      </AuthContext.Provider>
    );
    expect(screen.getByText('page1 화면입니다')).toBeInTheDocument();
    expect(screen.getByText('TestUser')).toBeInTheDocument();
  });

  it('renders guest name when no user is logged in', () => {
    render(
      <AuthContext.Provider value={{ user: null }}>
        <Feature1Page />
      </AuthContext.Provider>
    );
    expect(screen.getByText('page1 화면입니다')).toBeInTheDocument();
    expect(screen.getByText('Guest')).toBeInTheDocument();
  });
});
