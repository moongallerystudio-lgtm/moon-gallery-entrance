const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#chat-input");
const voiceButton = document.querySelector("#voice-button");
const voiceStatus = document.querySelector("#voice-status");
const avatar = document.querySelector("#avatar");
const quickTopics = document.querySelector("#quick-topics");
const languageButtons = document.querySelectorAll("[data-lang]");
const statusPill = document.querySelector("#status-pill");
const introCopy = document.querySelector("#intro-copy");
const welcomeMessage = document.querySelector("#welcome-message");
const hoursMeta = document.querySelector("#hours-meta");
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const speech = window.speechSynthesis;

let recognition = null;
let listening = false;
let wakeMode = false;
let awake = false;
let speakingTimer = null;
let sleepTimer = null;
let restartTimer = null;
let currentLanguage = "zh";
let currentVoiceLanguage = "zh-CN";
let scanIndex = 0;
let manuallyStopping = false;
let voiceUnavailableReason = "";
let cachedVoices = [];

const voiceLanguageMap = {
  zh: "zh-CN",
  ja: "ja-JP",
  en: "en-US",
};

const preferredVoiceNames = {
  zh: ["ting-ting", "meijia", "mei-jia", "sandy", "shelley", "flo", "sin-ji", "li-mu"],
  ja: ["kyoko", "sandy", "shelley", "flo", "otoya"],
  en: ["samantha", "ava", "allison", "karen", "moira", "tessa", "sandy", "shelley", "flo"],
};

const scanLanguages = ["zh", "ja", "en"];

const wakePhrases = {
  zh: ["你好", "您好", "哈喽", "嗨", "小兔", "moon", "hello"],
  ja: ["こんにちは", "こんばんは", "すみません", "ムーン", "moon", "hello"],
  en: ["hello", "hi", "hey", "moon", "excuse me"],
};

const voiceLabels = {
  zh: {
    idle: "开启唤醒",
    stop: "关闭唤醒",
    waiting: "唤醒已开启。请说“你好”来开始对话。",
    awake: "我在，请直接说你的问题。",
    thinking: "正在思考回答。",
    recognized: "听到了，正在回答。",
    sleeping: "已回到唤醒等待模式。",
    stopped: "语音唤醒已关闭。",
    denied: "麦克风权限未开启，请允许浏览器使用麦克风。",
    unavailable: "语音识别暂时不可用，请再试一次。",
    unsupported: "当前浏览器不支持网页语音识别，可使用 iPad 键盘自带听写。",
    insecure: "当前页面不是安全来源，浏览器会限制麦克风。请改用 HTTPS 地址。",
    unavailableButton: "不可用",
    network: "网络连接暂时不可用，请稍后再试或联系工作人员。",
  },
  ja: {
    idle: "音声起動",
    stop: "起動停止",
    waiting: "音声起動中です。「こんにちは」と話しかけてください。",
    awake: "はい、聞いています。質問をそのまま話してください。",
    thinking: "回答を考えています。",
    recognized: "聞き取りました。回答します。",
    sleeping: "音声起動待ちに戻りました。",
    stopped: "音声起動を停止しました。",
    denied: "マイクの権限がありません。ブラウザでマイクの使用を許可してください。",
    unavailable: "音声認識が一時的に使えません。もう一度お試しください。",
    unsupported: "このブラウザは音声認識に対応していません。iPadキーボードの音声入力をご利用ください。",
    insecure: "このページは安全な接続ではないため、ブラウザがマイクを制限しています。HTTPSで開いてください。",
    unavailableButton: "利用不可",
    network: "ネットワークに接続できません。少し待ってからもう一度お試しください。",
  },
  en: {
    idle: "Wake Voice",
    stop: "Stop Wake",
    waiting: "Wake mode is on. Say “hello” to start.",
    awake: "I am listening. Please ask your question.",
    thinking: "Thinking about the answer.",
    recognized: "I heard you. Answering now.",
    sleeping: "Back to wake mode.",
    stopped: "Voice wake mode is off.",
    denied: "Microphone permission is off. Please allow microphone access in the browser.",
    unavailable: "Voice recognition is temporarily unavailable. Please try again.",
    unsupported: "This browser does not support web voice recognition. You can use iPad keyboard dictation instead.",
    insecure: "This page is not a secure origin, so the browser restricts microphone access. Please use the HTTPS address.",
    unavailableButton: "Unavailable",
    network: "The network is temporarily unavailable. Please try again later or contact staff.",
  },
};

const uiText = {
  zh: {
    pageTitle: "Moon Gallery & Studio 入口接待",
    status: "入口接待中",
    intro: "Moon Gallery & Studio 为来自不同国家的艺术家提供展览、交流和实验性艺术项目的平台。我可以介绍展览、回答参观问题，或帮你呼叫工作人员。",
    welcome: "你好，我是 Moon Gallery 的虚拟接待员。请选择一个问题，或直接输入你想了解的内容。",
    placeholder: "输入问题，例如：今天几点关门？",
    send: "发送",
    voiceTitle: "开启语音唤醒",
    voiceHint: "点击开启唤醒后，说“你好”开始语音对话。",
    hours: "开放时间 展览期间通常 13:00 - 19:00，具体以当期展览公告为准",
    quickTopics: ["今天的展览介绍", "开放时间", "画廊地址", "可以拍照吗", "如何预约导览", "呼叫工作人员"],
  },
  ja: {
    pageTitle: "Moon Gallery & Studio 入口受付",
    status: "入口受付中",
    intro: "Moon Gallery & Studioは、さまざまな国のアーティストに展示、交流、実験的なアートプロジェクトの場を提供しています。展示案内や来館に関する質問、スタッフへの連絡をお手伝いできます。",
    welcome: "こんにちは。Moon Galleryのバーチャル受付です。質問を選ぶか、知りたいことを直接入力してください。",
    placeholder: "質問を入力してください。例：今日は何時までですか？",
    send: "送信",
    voiceTitle: "音声起動を開始",
    voiceHint: "音声起動を開始してから「こんにちは」と話しかけてください。",
    hours: "営業時間 展示期間中は通常 13:00 - 19:00、詳細は各展示案内をご確認ください",
    quickTopics: ["今日の展示案内", "営業時間", "ギャラリーの住所", "写真は撮れますか", "予約方法", "スタッフを呼ぶ"],
  },
  en: {
    pageTitle: "Moon Gallery & Studio Entrance Host",
    status: "Entrance Host",
    intro: "Moon Gallery & Studio provides a platform for artists from different countries through exhibitions, exchange, and experimental art projects. I can introduce the exhibition, answer visitor questions, or call staff.",
    welcome: "Hello, I am the virtual host for Moon Gallery. Choose a question or type what you would like to know.",
    placeholder: "Type a question, for example: What time do you close today?",
    send: "Send",
    voiceTitle: "Start Voice Wake",
    voiceHint: "After starting voice wake, say “hello” to begin a voice conversation.",
    hours: "Hours Usually 13:00 - 19:00 during exhibitions; please check the current exhibition notice",
    quickTopics: ["Today's exhibition", "Opening hours", "Gallery address", "Can I take photos?", "How to reserve", "Call staff"],
  },
};

function detectLanguage(text) {
  const trimmed = text.trim();
  if (!trimmed) return currentLanguage;
  if (/[\u3040-\u30ff]/.test(trimmed)) return "ja";
  const latin = (trimmed.match(/[A-Za-z]/g) || []).length;
  const cjk = (trimmed.match(/[\u4e00-\u9fff]/g) || []).length;
  if (latin >= 3 && latin > cjk) return "en";
  if (/\b(where|what|when|hello|hi|hey|ticket|photo|artist|open|hours|address)\b/i.test(trimmed)) return "en";
  if (/(です|ます|どこ|何時|営業時間|場所|予約|写真|展示|トイレ|作家|購入|講座)/.test(trimmed)) return "ja";
  return "zh";
}

function labelsFor(language) {
  return voiceLabels[language] || voiceLabels.zh;
}

function setAvatarMode(mode, active) {
  if (!avatar) return;
  avatar.classList.toggle(`is-${mode}`, active);
}

function pulseSpeaking() {
  if (!avatar) return;
  window.clearTimeout(speakingTimer);
  avatar.classList.add("is-speaking");
  speakingTimer = window.setTimeout(() => {
    avatar.classList.remove("is-speaking");
  }, 1400);
}

function addMessage(text, sender) {
  const item = document.createElement("article");
  item.className = `message ${sender}`;
  const span = document.createElement("span");
  span.textContent = text;
  item.appendChild(span);
  messages.appendChild(item);
  messages.scrollTop = messages.scrollHeight;
}

function applyLanguage(language) {
  currentLanguage = language || "zh";
  document.documentElement.lang = currentLanguage === "ja" ? "ja" : currentLanguage === "en" ? "en" : "zh-CN";
  currentVoiceLanguage = voiceLanguageMap[currentLanguage] || "zh-CN";
  if (recognition && !listening) {
    recognition.lang = currentVoiceLanguage;
  }
  applyInterfaceLanguage(currentLanguage);
  updateVoiceButton();
}

function applyInterfaceLanguage(language) {
  const copy = uiText[language] || uiText.zh;
  document.title = copy.pageTitle;
  if (statusPill) statusPill.textContent = copy.status;
  if (introCopy) introCopy.textContent = copy.intro;
  if (welcomeMessage) welcomeMessage.textContent = copy.welcome;
  if (input) input.placeholder = copy.placeholder;
  const submitButton = form?.querySelector("button[type='submit']");
  if (submitButton) submitButton.textContent = copy.send;
  if (voiceButton) {
    voiceButton.title = copy.voiceTitle;
    voiceButton.setAttribute("aria-label", copy.voiceTitle);
  }
  if (voiceStatus && !wakeMode) {
    voiceStatus.textContent = voiceUnavailableReason
      ? labelsFor(language)[voiceUnavailableReason]
      : copy.voiceHint;
  }
  if (hoursMeta) hoursMeta.textContent = copy.hours;
  if (quickTopics) {
    const buttons = quickTopics.querySelectorAll("button");
    copy.quickTopics.forEach((topic, index) => {
      const button = buttons[index];
      if (!button) return;
      button.textContent = topic;
      button.dataset.topic = topic;
    });
  }
  languageButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.lang === language);
    button.setAttribute("aria-pressed", button.dataset.lang === language ? "true" : "false");
  });
}

function updateVoiceButton() {
  if (!voiceButton) return;
  if (voiceUnavailableReason) {
    voiceButton.disabled = true;
    voiceButton.classList.remove("is-listening");
    voiceButton.textContent = labelsFor(currentLanguage).unavailableButton;
    voiceButton.title = labelsFor(currentLanguage)[voiceUnavailableReason];
    return;
  }
  voiceButton.classList.toggle("is-listening", wakeMode);
  voiceButton.textContent = wakeMode ? labelsFor(currentLanguage).stop : labelsFor(currentLanguage).idle;
}

function setVoiceStatus(text) {
  voiceStatus.textContent = text || "";
}

function cleanSpeechText(text) {
  return text
    .replace(/https?:\/\/\S+/g, "")
    .replace(/[*_`#>-]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function refreshVoices() {
  cachedVoices = speech?.getVoices ? speech.getVoices() : [];
}

function getPreferredVoice(language) {
  if (!speech?.getVoices) return null;

  const targetLang = voiceLanguageMap[language] || "zh-CN";
  const targetPrefix = targetLang.split("-")[0];
  const preferredNames = preferredVoiceNames[language] || [];
  const voices = cachedVoices.length ? cachedVoices : speech.getVoices();

  if (!voices.length) return null;

  const scoredVoices = voices
    .map((voice) => {
      const voiceName = voice.name.toLowerCase();
      const voiceLang = voice.lang.toLowerCase();
      const exactLanguage = voiceLang === targetLang.toLowerCase();
      const sameLanguage = voiceLang.startsWith(targetPrefix);
      const nameIndex = preferredNames.findIndex((name) => voiceName.includes(name));
      const preferredName = nameIndex >= 0 ? 50 - nameIndex : 0;
      const localBonus = voice.localService ? 4 : 0;

      return {
        voice,
        score: (exactLanguage ? 100 : 0) + (sameLanguage ? 30 : 0) + preferredName + localBonus,
      };
    })
    .filter(({ score }) => score > 0)
    .sort((a, b) => b.score - a.score);

  return scoredVoices[0]?.voice || null;
}

if (speech) {
  refreshVoices();
  speech.addEventListener?.("voiceschanged", refreshVoices);
}

function speak(text, language = currentLanguage, onEnd) {
  const speechText = cleanSpeechText(text);
  if (!speech || !speechText) {
    if (onEnd) onEnd();
    return;
  }

  speech.cancel();
  const utterance = new SpeechSynthesisUtterance(speechText);
  utterance.lang = voiceLanguageMap[language] || "zh-CN";
  const preferredVoice = getPreferredVoice(language);
  if (preferredVoice) {
    utterance.voice = preferredVoice;
    utterance.lang = preferredVoice.lang;
  }
  utterance.rate = language === "ja" ? 0.86 : 0.9;
  utterance.pitch = 1.18;
  utterance.onstart = () => setAvatarMode("speaking", true);
  utterance.onend = () => {
    setAvatarMode("speaking", false);
    if (onEnd) onEnd();
  };
  utterance.onerror = () => {
    setAvatarMode("speaking", false);
    if (onEnd) onEnd();
  };
  speech.speak(utterance);
}

function isWakePhrase(text) {
  const normalized = text.trim().toLowerCase();
  if (!normalized) return false;
  return Object.values(wakePhrases).some((phrases) =>
    phrases.some((phrase) => normalized.includes(phrase.toLowerCase()))
  );
}

function wakeUp(language) {
  awake = true;
  applyLanguage(language);
  window.clearTimeout(sleepTimer);
  const message = labelsFor(language).awake;
  addMessage(message, "bot");
  setVoiceStatus(message);
  speak(message, language, () => {
    scheduleSleep();
    restartWakeListening(300);
  });
}

function scheduleSleep() {
  window.clearTimeout(sleepTimer);
  sleepTimer = window.setTimeout(() => {
    awake = false;
    setVoiceStatus(labelsFor(currentLanguage).sleeping);
  }, 30000);
}

async function ask(message, options = {}) {
  const text = message.trim();
  if (!text) return;

  const userLanguage = detectLanguage(text);
  applyLanguage(userLanguage);
  addMessage(text, "user");
  input.value = "";
  setAvatarMode("thinking", true);
  setVoiceStatus(labelsFor(userLanguage).thinking);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await response.json();
    const replyLanguage = data.language || userLanguage;
    applyLanguage(replyLanguage);
    addMessage(data.reply, "bot");
    pulseSpeaking();
    if (options.fromVoice) {
      speak(data.reply, replyLanguage, () => {
        scheduleSleep();
        restartWakeListening(500);
      });
    }
  } catch (error) {
    const messageText = labelsFor(userLanguage).network;
    addMessage(messageText, "bot");
    pulseSpeaking();
    if (options.fromVoice) {
      speak(messageText, userLanguage, () => restartWakeListening(500));
    }
  } finally {
    setAvatarMode("thinking", false);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  ask(input.value);
});

quickTopics?.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-topic]");
  if (button) ask(button.dataset.topic);
});

languageButtons.forEach((button) => {
  button.addEventListener("click", () => {
    applyLanguage(button.dataset.lang);
    if (wakeMode) {
      awake = false;
      stopRecognition();
      setVoiceStatus(labelsFor(currentLanguage).waiting);
      restartWakeListening(300);
    }
  });
});

function startRecognition(language) {
  if (!recognition || listening) return;
  const nextLanguage = language || (awake ? currentLanguage : scanLanguages[scanIndex]);
  recognition.lang = voiceLanguageMap[nextLanguage] || "zh-CN";
  recognition.continuous = false;
  recognition.interimResults = true;
  try {
    manuallyStopping = false;
    recognition.start();
  } catch (error) {
    restartWakeListening(700);
  }
}

function stopRecognition() {
  if (!recognition || !listening) return;
  manuallyStopping = true;
  recognition.stop();
}

function restartWakeListening(delay = 500) {
  window.clearTimeout(restartTimer);
  if (!wakeMode || !recognition) return;
  restartTimer = window.setTimeout(() => {
    if (!wakeMode || listening || speech?.speaking) return;
    if (!awake) {
      scanIndex = (scanIndex + 1) % scanLanguages.length;
    }
    startRecognition(awake ? currentLanguage : scanLanguages[scanIndex]);
  }, delay);
}

if (SpeechRecognition && window.isSecureContext) {
  recognition = new SpeechRecognition();

  recognition.addEventListener("start", () => {
    listening = true;
    setAvatarMode("listening", true);
    updateVoiceButton();
    const activeLanguage = Object.entries(voiceLanguageMap).find(([, value]) => value === recognition.lang)?.[0] || currentLanguage;
    setVoiceStatus(awake ? labelsFor(activeLanguage).awake : labelsFor(activeLanguage).waiting);
  });

  recognition.addEventListener("result", (event) => {
    let finalText = "";
    let interimText = "";

    for (let index = event.resultIndex; index < event.results.length; index += 1) {
      const transcript = event.results[index][0].transcript.trim();
      if (event.results[index].isFinal) {
        finalText += transcript;
      } else {
        interimText += transcript;
      }
    }

    input.value = finalText || interimText;

    if (!finalText) return;

    const detectedLanguage = detectLanguage(finalText);
    applyLanguage(detectedLanguage);

    if (!awake) {
      if (isWakePhrase(finalText)) {
        stopRecognition();
        wakeUp(detectedLanguage);
      } else {
        manuallyStopping = false;
        recognition.stop();
        restartWakeListening(900);
      }
      return;
    }

    stopRecognition();
    setVoiceStatus(labelsFor(detectedLanguage).recognized);
    window.clearTimeout(sleepTimer);
    ask(finalText, { fromVoice: true });
  });

  recognition.addEventListener("end", () => {
    listening = false;
    setAvatarMode("listening", false);
    updateVoiceButton();
    if (wakeMode && !manuallyStopping) {
      restartWakeListening(600);
    }
    manuallyStopping = false;
  });

  recognition.addEventListener("error", (event) => {
    listening = false;
    setAvatarMode("listening", false);
    const labels = labelsFor(currentLanguage);
    setVoiceStatus(event.error === "not-allowed" ? labels.denied : labels.unavailable);
    updateVoiceButton();
    if (wakeMode && event.error !== "not-allowed") {
      restartWakeListening(1200);
    }
  });

  voiceButton.addEventListener("click", () => {
    wakeMode = !wakeMode;
    if (!wakeMode) {
      awake = false;
      window.clearTimeout(sleepTimer);
      window.clearTimeout(restartTimer);
      speech?.cancel();
      stopRecognition();
      setAvatarMode("listening", false);
      setAvatarMode("speaking", false);
      setVoiceStatus(labelsFor(currentLanguage).stopped);
      updateVoiceButton();
      return;
    }

    scanIndex = 0;
    awake = false;
    updateVoiceButton();
    setVoiceStatus(labelsFor(currentLanguage).waiting);
    startRecognition(scanLanguages[scanIndex]);
  });
} else {
  voiceUnavailableReason = window.isSecureContext ? "unsupported" : "insecure";
  voiceButton.disabled = true;
}

applyLanguage("zh");
