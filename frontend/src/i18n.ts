import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const resources = {
  en: {
    translation: {
      app_title: "NICE HRIS",
      subtitle: "Bangladesh Multi-Tenant HRM SaaS",
      search_placeholder: "Jump to any of the 42 modules or search employees (Ctrl+K)...",
      company_switcher: "Legal Entity",
      single_company_badge: "Single-Company Tenant",
      multi_company_badge: "Multi-Company Group",
      lakh_grouping: "BDT Lakh Format",
      design_system: "Design System",
      platform_admin: "Platform Admin",
    },
  },
  bn: {
    translation: {
      app_title: "নাইস এইচআরআইএস",
      subtitle: "বাংলাদেশ মাল্টি-টেন্যান্ট মানবসম্পদ ব্যবস্থাপনা",
      search_placeholder: "যেকোনো মডিউল বা কর্মী খুঁজুন (Ctrl+K)...",
      company_switcher: "প্রতিষ্ঠান নির্বাচন",
      single_company_badge: "একক প্রতিষ্ঠান টেন্যান্ট",
      multi_company_badge: "মাল্টি-কোম্পানি গ্রুপ",
      lakh_grouping: "লাখ ফরম্যাট (টাকা)",
      design_system: "ডিজাইন সিস্টেম",
      platform_admin: "প্ল্যাটফর্ম অ্যাডমিন",
    },
  },
};

i18n.use(initReactI18next).init({
  resources,
  lng: "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

/**
 * Formats a number or numeric string as BDT with South Asian Lakh/Crore grouping (e.g. ৳ 1,25,000.00)
 */
export function formatBDT(value: number | string | undefined | null, useLakh = true): string {
  if (value === undefined || value === null) return "৳ 0.00";
  if (typeof value === "string" && value.includes("Restricted")) return value;
  const num = typeof value === "number" ? value : parseFloat(value);
  if (Number.isNaN(num)) return String(value);

  const formatted = new Intl.NumberFormat(useLakh ? "en-IN" : "en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
  return `৳ ${formatted}`;
}

export default i18n;
