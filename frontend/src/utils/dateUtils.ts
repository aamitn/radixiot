export const formatDateTimeForAPI = (dateTimeStr: string): string => {
  if (!dateTimeStr) return '';
  // Convert from "2025-09-29T22:27:44" to "2025-09-29 22:27:44"
  return dateTimeStr.replace('T', ' ');
};

export const getCurrentDateTime = (): string => {
  return new Date().toISOString().slice(0, 19); // Format: "2025-09-29T22:27:44"
};
