import { User } from '@/types';

jest.mock('@/utils/storage', () => ({
  setToken: jest.fn().mockResolvedValue(undefined),
  deleteToken: jest.fn().mockResolvedValue(undefined),
  getToken: jest.fn().mockResolvedValue(null),
  setServerUrl: jest.fn().mockResolvedValue(undefined),
  deleteServerUrl: jest.fn().mockResolvedValue(undefined),
  getPushToken: jest.fn().mockResolvedValue(null),
  deletePushToken: jest.fn().mockResolvedValue(undefined),
}));

jest.mock('@/api/uploads', () => ({
  refreshMediaToken: jest.fn().mockResolvedValue(undefined),
}));

jest.mock('@famlin/api-client', () => ({
  setApiBaseUrl: jest.fn(),
  setMediaToken: jest.fn(),
  unregisterPushToken: jest.fn().mockResolvedValue(undefined),
}));

const testUser: User = {
  id: 'u1',
  email: 'a@example.com',
  name: 'Alice',
  isAdmin: false,
  hasPassword: true,
  emailOnNewPost: true,
  emailOnNewComment: true,
  emailOnNewLike: true,
  pushOnNewPost: true,
  pushOnNewComment: true,
  pushOnNewLike: true,
};

describe('authStore', () => {
  beforeEach(() => {
    jest.resetModules();
    jest.clearAllMocks();
  });

  it('setAuth stores the token/server, sets the api base URL, updates state, and refreshes the media token', async () => {
    const storage = jest.requireMock('@/utils/storage');
    const client = jest.requireMock('@famlin/api-client');
    const uploads = jest.requireMock('@/api/uploads');
    const { useAuthStore } = jest.requireActual('@/stores/authStore');

    await useAuthStore.getState().setAuth(testUser, 'tok-abc', 'http://example.com');

    expect(storage.setToken).toHaveBeenCalledWith('tok-abc');
    expect(storage.setServerUrl).toHaveBeenCalledWith('http://example.com');
    expect(client.setApiBaseUrl).toHaveBeenCalledWith('http://example.com');
    expect(uploads.refreshMediaToken).toHaveBeenCalledTimes(1);

    const state = useAuthStore.getState();
    expect(state.user).toEqual(testUser);
    expect(state.token).toBe('tok-abc');
    expect(state.serverUrl).toBe('http://example.com');
    expect(state.isLoading).toBe(false);
  });

  it('logout deletes the token AND the server URL and resets state', async () => {
    const storage = jest.requireMock('@/utils/storage');
    const client = jest.requireMock('@famlin/api-client');
    storage.getPushToken.mockResolvedValue(null); // no push token registered
    const { useAuthStore } = jest.requireActual('@/stores/authStore');

    await useAuthStore.getState().setAuth(testUser, 'tok-abc', 'http://example.com');
    await useAuthStore.getState().logout();

    expect(storage.deleteToken).toHaveBeenCalledTimes(1);
    expect(storage.deleteServerUrl).toHaveBeenCalledTimes(1);
    expect(client.setMediaToken).toHaveBeenCalledWith(null);

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.serverUrl).toBeNull();
  });

  it('logout also unregisters this device push token when one is stored', async () => {
    const storage = jest.requireMock('@/utils/storage');
    const client = jest.requireMock('@famlin/api-client');
    storage.getPushToken.mockResolvedValue('push-token-xyz');
    const { useAuthStore } = jest.requireActual('@/stores/authStore');

    await useAuthStore.getState().logout();

    expect(client.unregisterPushToken).toHaveBeenCalledWith('push-token-xyz');
    expect(storage.deletePushToken).toHaveBeenCalledTimes(1);
  });

  it('clearSession deletes the token but PRESERVES the server URL', async () => {
    const storage = jest.requireMock('@/utils/storage');
    const client = jest.requireMock('@famlin/api-client');
    const { useAuthStore } = jest.requireActual('@/stores/authStore');

    await useAuthStore.getState().setAuth(testUser, 'tok-abc', 'http://example.com');
    await useAuthStore.getState().clearSession();

    expect(storage.deleteToken).toHaveBeenCalledTimes(1);
    expect(storage.deleteServerUrl).not.toHaveBeenCalled();
    expect(client.setMediaToken).toHaveBeenCalledWith(null);

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    // serverUrl is intentionally left as-is (not reset to null in clearSession).
    expect(state.serverUrl).toBe('http://example.com');
  });
});
