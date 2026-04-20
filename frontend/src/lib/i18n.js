export const languages = ["English", "Hindi", "Bengali", "Odia"];

export const models = [
  "anthropic/claude-3-opus",
  "anthropic/claude-3-sonnet",
  "openai/gpt-4-turbo-preview",
  "google/gemini-pro",
  "meta-llama/llama-3-70b-instruct"
];

const dictionary = {
  English: {},
  Hindi: {
    "Upload & Settings": "अपलोड और सेटिंग्स",
    "Upload Data": "डेटा अपलोड करें",
    "Financial Settings": "वित्तीय सेटिंग्स",
    "Add New Transaction": "नई ट्रांज़ैक्शन जोड़ें",
    "Manage Financial Goals": "वित्तीय लक्ष्य प्रबंधित करें",
    "Manage Bill Reminders": "बिल रिमाइंडर प्रबंधित करें",
    "Manage Category Budgets": "श्रेणी बजट प्रबंधित करें",
    "Dashboard Overview": "डैशबोर्ड अवलोकन",
    "Smart Insights & Alerts": "स्मार्ट इनसाइट्स और अलर्ट",
    "AI Assistant": "एआई सहायक"
  },
  Bengali: {
    "Upload & Settings": "আপলোড ও সেটিংস",
    "Upload Data": "ডেটা আপলোড",
    "Financial Settings": "আর্থিক সেটিংস",
    "Add New Transaction": "নতুন লেনদেন যোগ করুন",
    "Manage Financial Goals": "আর্থিক লক্ষ্য পরিচালনা",
    "Manage Bill Reminders": "বিল রিমাইন্ডার পরিচালনা",
    "Manage Category Budgets": "ক্যাটাগরি বাজেট পরিচালনা",
    "Dashboard Overview": "ড্যাশবোর্ড ওভারভিউ",
    "Smart Insights & Alerts": "স্মার্ট ইনসাইটস ও অ্যালার্ট",
    "AI Assistant": "এআই সহায়ক"
  },
  Odia: {
    "Upload & Settings": "ଅପଲୋଡ୍ ଏବଂ ସେଟିଂସ୍",
    "Upload Data": "ଡାଟା ଅପଲୋଡ୍",
    "Financial Settings": "ଆର୍ଥିକ ସେଟିଂସ୍",
    "Add New Transaction": "ନୂତନ ଟ୍ରାଞ୍ଜାକ୍ସନ୍ ଯୋଡନ୍ତୁ",
    "Manage Financial Goals": "ଆର୍ଥିକ ଲକ୍ଷ୍ୟ ପରିଚାଳନା",
    "Manage Bill Reminders": "ବିଲ୍ ରିମାଇଣ୍ଡର ପରିଚାଳନା",
    "Manage Category Budgets": "ଶ୍ରେଣୀ ବଜେଟ୍ ପରିଚାଳନା",
    "Dashboard Overview": "ଡ୍ୟାଶବୋର୍ଡ ଅଭିଲୋକନ",
    "Smart Insights & Alerts": "ସ୍ମାର୍ଟ ଇନସାଇଟ୍ସ ଏବଂ ଆଲର୍ଟ",
    "AI Assistant": "ଏଆଇ ସହାୟକ"
  }
};

export function t(language, text) {
  return dictionary[language]?.[text] || text;
}
