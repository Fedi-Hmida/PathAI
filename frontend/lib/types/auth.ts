export type AuthConfig = {
  enabled: boolean;
};

export type UserDTO = {
  user_id: string;
  email: string;
  created_at: string;
  updated_at: string;
};

export type AuthSessionResponse = {
  user: UserDTO;
  access_token: string;
  token_type: string;
  expires_in: number;
};

export type RegisterRequest = {
  email: string;
  password: string;
};

export type LoginRequest = {
  email: string;
  password: string;
};
