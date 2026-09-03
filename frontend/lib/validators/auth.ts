export function validatePasswordLength(password: string): string | null { return password.length >= 12 && password.length <= 128 ? null : "Password must be between 12 and 128 characters."; }
