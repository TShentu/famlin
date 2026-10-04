import { useEffect } from 'react';
import { AppState } from 'react-native';
import { checkForAppUpdate } from '@/utils/appUpdates';

export function useAppUpdates(ready: boolean) {
  useEffect(() => {
    if (!ready) return;
    void checkForAppUpdate();
    const subscription = AppState.addEventListener('change', (state) => {
      if (state === 'active') void checkForAppUpdate();
    });
    return () => subscription.remove();
  }, [ready]);
}
