export {};

declare global {
  namespace google.accounts.id {
    interface CredentialResponse {
      credential: string;
      select_by: string;
      clientId?: string;
    }

    interface GsiButtonConfiguration {
      type?: 'standard' | 'icon';
      theme?: 'outline' | 'filled_blue' | 'filled_black';
      size?: 'large' | 'medium' | 'small';
      text?: 'signin_with' | 'signup_with' | 'continue_with' | 'signin';
      shape?: 'rectangular' | 'pill' | 'circle' | 'square';
      logo_alignment?: 'left' | 'center';
      width?: number | string;
      locale?: string;
    }
  }

  interface Window {
    google?: {
      accounts: {
        id: {
          initialize(options: {
            client_id: string;
            callback: (response: google.accounts.id.CredentialResponse) => void;
            auto_select?: boolean;
            cancel_on_tap_outside?: boolean;
            use_fedcm_for_prompt?: boolean;
          }): void;
          renderButton(container: HTMLElement, options: google.accounts.id.GsiButtonConfiguration): void;
          prompt(): void;
          cancel(): void;
          disableAutoSelect(): void;
        };
      };
    };
  }
}
