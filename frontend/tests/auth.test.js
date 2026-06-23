import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginPage from '../src/app/login/page';
import JoinPage from '../src/app/join/page';
import { AuthContext } from '../src/contexts/AuthContext';
import authApi from '../src/apis/authApi';
import memberApi from '../src/apis/memberApi';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      prefetch: () => null,
      replace: jest.fn(),
      push: jest.fn(),
    };
  },
  usePathname() {
    return '/login';
  },
}));

// Mock Link
jest.mock('next/link', () => {
  return ({ children, href }) => {
    return <a href={href}>{children}</a>;
  };
});

// Mock api modules
jest.mock('../src/apis/authApi');
jest.mock('../src/apis/memberApi');

describe('Auth Pages Unit Tests', () => {
  const mockSetUser = jest.fn();
  const mockSetAccessToken = jest.fn();
  const authContextValue = {
    setUser: mockSetUser,
    setAccessToken: mockSetAccessToken,
    user: '',
    accessToken: '',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('LoginPage', () => {
    it('renders login form items correctly', () => {
      render(
        <AuthContext.Provider value={authContextValue}>
          <LoginPage />
        </AuthContext.Provider>
      );

      expect(screen.getByPlaceholderText(/아이디를 입력하세요/)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/비밀번호를 입력하세요/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '로그인' })).toBeInTheDocument();
    });

    it('shows validation warning when fields are blank', async () => {
      render(
        <AuthContext.Provider value={authContextValue}>
          <LoginPage />
        </AuthContext.Provider>
      );

      fireEvent.click(screen.getByRole('button', { name: '로그인' }));
      expect(await screen.findByText('아이디와 비밀번호를 모두 입력해주세요.')).toBeInTheDocument();
    });

    it('calls authApi.login and sets context on success', async () => {
      authApi.login.mockResolvedValue({
        username: 'test-user',
        access_token: 'valid-token',
      });

      render(
        <AuthContext.Provider value={authContextValue}>
          <LoginPage />
        </AuthContext.Provider>
      );

      fireEvent.change(screen.getByPlaceholderText(/아이디를 입력하세요/), {
        target: { value: 'testuser' },
      });
      fireEvent.change(screen.getByPlaceholderText(/비밀번호를 입력하세요/), {
        target: { value: 'password123' },
      });
      fireEvent.click(screen.getByRole('button', { name: '로그인' }));

      await waitFor(() => {
        expect(authApi.login).toHaveBeenCalledWith('testuser', 'password123');
        expect(mockSetUser).toHaveBeenCalledWith('test-user');
        expect(mockSetAccessToken).toHaveBeenCalledWith('valid-token');
      });
    });
  });

  describe('JoinPage', () => {
    it('renders signup form items correctly', () => {
      render(
        <AuthContext.Provider value={authContextValue}>
          <JoinPage />
        </AuthContext.Provider>
      );

      expect(screen.getAllByPlaceholderText(/5~20자 사이로 입력하세요/)[0]).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/2~20자 사이로 입력하세요/)).toBeInTheDocument();
      expect(screen.getByPlaceholderText('example@domain.com')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '가입하기' })).toBeInTheDocument();
    });

    it('shows validation warning when fields are short', async () => {
      render(
        <AuthContext.Provider value={authContextValue}>
          <JoinPage />
        </AuthContext.Provider>
      );

      fireEvent.change(screen.getAllByPlaceholderText(/5~20자 사이로 입력하세요/)[0], {
        target: { value: 'abc' },
      });
      fireEvent.change(screen.getByPlaceholderText(/2~20자 사이로 입력하세요/), {
        target: { value: 'a' },
      });
      fireEvent.change(screen.getByPlaceholderText('example@domain.com'), {
        target: { value: 'test@domain.com' },
      });
      fireEvent.change(screen.getAllByPlaceholderText(/5~20자 사이로 입력하세요/)[1], {
        target: { value: '123' },
      });

      fireEvent.click(screen.getByRole('button', { name: '가입하기' }));
      expect(await screen.findByText('아이디는 최소 5자 이상이어야 합니다.')).toBeInTheDocument();
    });

    it('calls memberApi.join and registers account successfully', async () => {
      memberApi.join.mockResolvedValue({ status: 'success' });
      authApi.login.mockResolvedValue({
        username: 'newuser',
        access_token: 'new-token',
      });

      render(
        <AuthContext.Provider value={authContextValue}>
          <JoinPage />
        </AuthContext.Provider>
      );

      fireEvent.change(screen.getAllByPlaceholderText(/5~20자 사이로 입력하세요/)[0], {
        target: { value: 'newuser123' },
      });
      fireEvent.change(screen.getByPlaceholderText(/2~20자 사이로 입력하세요/), {
        target: { value: 'NewName' },
      });
      fireEvent.change(screen.getByPlaceholderText('example@domain.com'), {
        target: { value: 'new@domain.com' },
      });
      fireEvent.change(screen.getAllByPlaceholderText(/5~20자 사이로 입력하세요/)[1], {
        target: { value: 'securepwd' },
      });

      fireEvent.click(screen.getByRole('button', { name: '가입하기' }));

      await waitFor(() => {
        expect(memberApi.join).toHaveBeenCalledWith({
          mid: 'newuser123',
          mname: 'NewName',
          memail: 'new@domain.com',
          mpassword: 'securepwd',
          menabled: true,
          mrole: 'ROLE_USER',
        });
        expect(authApi.login).toHaveBeenCalledWith('newuser123', 'securepwd');
      });
    });
  });
});
