// Base backend error model
export interface BackendErrorBody {
  success: boolean;
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
  request_id?: string;
}

// User role enum placeholder
export enum UserRole {
  VIEWER = "VIEWER",
  EDITOR = "EDITOR",
  ADMIN = "ADMIN",
}

// Base user model
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
