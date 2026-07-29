import express from "express";
import path from "path";
import fs from "fs";
import cors from "cors";
import { GoogleGenAI } from "@google/genai";

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json({ limit: "10mb" }));

// In-memory state for settings, context, etc.
let appSettings: Record<string, any> = {
  model: "auto",
  temperature: 0.7,
  ui_lang: "vi",
  learn_lang: "en",
};

let appContext: Record<string, any> | null = null;

// Built-in vocabulary samples for decks
const BUILTIN_DECKS = [
  { id: 1, name: "English Core Vocabulary", level: 0 },
  { id: 2, name: "IELTS Essential 500", level: 0 },
  { id: 3, name: "Business English", level: 0 },
  { id: 4, name: "Daily Conversation", level: 0 },
];

const VOCAB_POOLS: Record<number, Array<{ id: number; key: string; term: string; definition: string }>> = {
  1: [
    { id: 1, key: "ubiquitous\0present everywhere", term: "ubiquitous", definition: "present, appearing, or found everywhere" },
    { id: 2, key: "pragmatic\0practical approach", term: "pragmatic", definition: "dealing with things sensibly and realistically" },
    { id: 3, key: "ambiguous\0open to interpretations", term: "ambiguous", definition: "open to more than one interpretation; unclear" },
    { id: 4, key: "eloquent\0fluent or persuasive", term: "eloquent", definition: "fluent or persuasive in speaking or writing" },
    { id: 5, key: "resilient\0quick to recover", term: "resilient", definition: "able to withstand or recover quickly from difficult conditions" },
    { id: 6, key: "ephemeral\0lasting a short time", term: "ephemeral", definition: "lasting for a very short time" },
    { id: 7, key: "consensus\0general agreement", term: "consensus", definition: "a general agreement among a group of people" },
    { id: 8, key: "deteriorate\0become worse", term: "deteriorate", definition: "to become progressively worse" },
    { id: 9, key: "scrutiny\0critical observation", term: "scrutiny", definition: "critical observation or examination" },
    { id: 10, key: "advocate\0publicly support", term: "advocate", definition: "to publicly recommend or support a cause or policy" },
    { id: 11, key: "inevitable\0unavoidable", term: "inevitable", definition: "certain to happen; unavoidable" },
    { id: 12, key: "mitigate\0make less severe", term: "mitigate", definition: "to make less severe, serious, or painful" },
  ],
  2: [
    { id: 13, key: "paradigm\0typical pattern", term: "paradigm", definition: "a typical example or pattern of something" },
    { id: 14, key: "verbose\0using too many words", term: "verbose", definition: "using or expressed in more words than are needed" },
    { id: 15, key: "concise\0brief and clear", term: "concise", definition: "giving a lot of information clearly and in a few words" },
    { id: 16, key: "hypothesis\0proposed explanation", term: "hypothesis", definition: "a proposed explanation made on the basis of limited evidence" },
    { id: 17, key: "comprehensive\0complete and thorough", term: "comprehensive", definition: "including or dealing with all or nearly all elements or aspects" },
    { id: 18, key: "perceive\0become aware of", term: "perceive", definition: "to interpret or look at something in a particular way" },
    { id: 19, key: "plausible\0seeming reasonable", term: "plausible", definition: "seeming reasonable or probable" },
    { id: 20, key: "articulate\0express clearly", term: "articulate", definition: "having or showing the ability to speak fluently and coherently" },
  ],
  3: [
    { id: 21, key: "leverage\0use to advantage", term: "leverage", definition: "use something to maximum advantage" },
    { id: 22, key: "synergy\0combined interaction", term: "synergy", definition: "interaction or cooperation giving a greater combined effect" },
    { id: 23, key: "benchmark\0standard of reference", term: "benchmark", definition: "a standard or point of reference against which things may be compared" },
    { id: 24, key: "feasible\0possible to do easily", term: "feasible", definition: "possible and practical to do easily or conveniently" },
    { id: 25, key: "revenue\0income of organization", term: "revenue", definition: "income generated from normal business operations" },
  ],
  4: [
    { id: 26, key: "appreciated\0grateful for", term: "appreciated", definition: "recognized with gratitude" },
    { id: 27, key: "hesitate\0pause before doing", term: "hesitate", definition: "pause before saying or doing something due to uncertainty" },
    { id: 28, key: "recommend\0suggest as good", term: "recommend", definition: "advise or suggest something as a good choice" },
    { id: 29, key: "convenient\0fitting well with plans", term: "convenient", definition: "fitting in well with a person's needs, activities, or plans" },
    { id: 30, key: "opportunity\0favorable chance", term: "opportunity", definition: "a set of circumstances that makes it possible to do something" },
  ]
};

function getAiClient() {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) return null;
  return new GoogleGenAI({ apiKey });
}

// Schemas for Gemini Structured Output
const SCHEMAS: Record<string, any> = {
  fill_blank: {
    type: "object",
    properties: {
      questions: {
        type: "array",
        items: {
          type: "object",
          properties: {
            sentence: { type: "string", description: "The sentence with _____ blank." },
            options: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  word: { type: "string" },
                  is_correct: { type: "boolean" },
                  type: { type: "string" },
                  reason: { type: "string" }
                },
                required: ["word", "is_correct", "type", "reason"]
              }
            },
            meaning_vi: { type: "string" },
            explanation_vi: { type: "string" },
            grammar_note: { type: "string" }
          },
          required: ["sentence", "options", "meaning_vi", "explanation_vi"]
        }
      }
    },
    required: ["questions"]
  },
  cloze: {
    type: "object",
    properties: {
      paragraph: { type: "string" },
      full_solution_text: { type: "string" },
      story_translation: { type: "string" },
      blanks: {
        type: "array",
        items: {
          type: "object",
          properties: {
            blank_id: { type: "integer" },
            answer: { type: "string" },
            options: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  word: { type: "string" },
                  is_correct: { type: "boolean" },
                  type: { type: "string" },
                  reason: { type: "string" }
                },
                required: ["word", "is_correct", "type", "reason"]
              }
            },
            meaning_vi: { type: "string" },
            explanation_vi: { type: "string" }
          },
          required: ["blank_id", "answer", "options", "meaning_vi", "explanation_vi"]
        }
      }
    },
    required: ["paragraph", "full_solution_text", "story_translation", "blanks"]
  },
  translation: {
    type: "object",
    properties: {
      source_sentence: { type: "string" },
      reference_translation: { type: "string" },
      alternative_translations: {
        type: "array",
        items: {
          type: "object",
          properties: {
            text: { type: "string" },
            note: { type: "string" }
          },
          required: ["text", "note"]
        }
      },
      key_vocabulary: {
        type: "array",
        items: {
          type: "object",
          properties: {
            word: { type: "string" },
            meaning_vi: { type: "string" },
            note: { type: "string" }
          },
          required: ["word", "meaning_vi", "note"]
        }
      },
      common_mistakes: {
        type: "array",
        items: {
          type: "object",
          properties: {
            wrong: { type: "string" },
            correction: { type: "string" },
            error_type: { type: "string" },
            feedback: { type: "string" }
          },
          required: ["wrong", "correction", "error_type", "feedback"]
        }
      },
      grading_rubric: { type: "string" }
    },
    required: ["source_sentence", "reference_translation", "alternative_translations", "key_vocabulary", "common_mistakes", "grading_rubric"]
  },
  unscramble: {
    type: "object",
    properties: {
      questions: {
        type: "array",
        items: {
          type: "object",
          properties: {
            correct_sentence: { type: "string" },
            shuffled_words: {
              type: "array",
              items: { type: "string" }
            },
            hint: { type: "string" },
            meaning_vi: { type: "string" },
            difficulty_reason: { type: "string" },
            grammar_note: { type: "string" },
            key_vocabulary: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  word: { type: "string" },
                  meaning_vi: { type: "string" }
                },
                required: ["word", "meaning_vi"]
              }
            }
          },
          required: ["correct_sentence", "shuffled_words", "hint", "meaning_vi", "difficulty_reason", "grammar_note", "key_vocabulary"]
        }
      }
    },
    required: ["questions"]
  },
  story: {
    type: "object",
    properties: {
      story: {
        type: "object",
        properties: {
          title: { type: "string" },
          content: { type: "string" },
          highlighted_vocab: {
            type: "array",
            items: {
              type: "object",
              properties: {
                word: { type: "string" },
                meaning_vi: { type: "string" },
                context_meaning: { type: "string" }
              },
              required: ["word", "meaning_vi", "context_meaning"]
            }
          },
          full_translation: { type: "string" }
        },
        required: ["title", "content", "highlighted_vocab", "full_translation"]
      },
      questions: {
        type: "array",
        items: {
          type: "object",
          properties: {
            question: { type: "string" },
            options: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  text: { type: "string" },
                  is_correct: { type: "boolean" }
                },
                required: ["text", "is_correct"]
              }
            },
            explanation: { type: "string" },
            evidence_quote: { type: "string" },
            type: { type: "string" }
          },
          required: ["question", "options", "explanation", "evidence_quote", "type"]
        }
      },
      discussion_prompt: { type: "string" }
    },
    required: ["story", "questions", "discussion_prompt"]
  },
  sentence_transform: {
    type: "object",
    properties: {
      questions: {
        type: "array",
        items: {
          type: "object",
          properties: {
            original: { type: "string" },
            prompt: { type: "string" },
            expected_answer: { type: "string" },
            normalized_answer: { type: "string" },
            grammar_rule: { type: "string" },
            acceptable_variations: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  text: { type: "string" },
                  note: { type: "string" }
                },
                required: ["text", "note"]
              }
            },
            common_errors: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  error: { type: "string" },
                  feedback: { type: "string" }
                },
                required: ["error", "feedback"]
              }
            }
          },
          required: ["original", "prompt", "expected_answer", "normalized_answer", "grammar_rule", "acceptable_variations", "common_errors"]
        }
      }
    },
    required: ["questions"]
  },
  taboo: {
    type: "object",
    properties: {
      rounds: {
        type: "array",
        items: {
          type: "object",
          properties: {
            target_word: { type: "string" },
            taboo_words: {
              type: "array",
              items: { type: "string" }
            },
            clue: { type: "string" },
            meaning_vi: { type: "string" },
            sample_acceptable_phrases: {
              type: "array",
              items: { type: "string" }
            },
            sample_forbidden_phrases: {
              type: "array",
              items: { type: "string" }
            }
          },
          required: ["target_word", "taboo_words", "clue", "meaning_vi", "sample_acceptable_phrases", "sample_forbidden_phrases"]
        }
      }
    },
    required: ["rounds"]
  }
};

// Helper function: Fisher-Yates mathematical random shuffle algorithm
function shuffleArray<T>(array: T[]): T[] {
  const result = [...array];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

// XSS Sanitization helper for AI content
function sanitizeHtml(htmlContent: string): string {
  if (!htmlContent || typeof htmlContent !== "string") return htmlContent || "";
  let clean = htmlContent.replace(/<(script|iframe|object|embed|style|link|form|input|button)\b[^<]*(?:(?!<\/\1>)<[^<]*)*<\/\1>/gi, "");
  clean = clean.replace(/<(script|iframe|object|embed|style|link|form|input|button)\b[^>]*\/?>/gi, "");
  clean = clean.replace(/\s*on\w+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, "");
  clean = clean.replace(/(href|src|action)\s*=\s*["']?\s*javascript:[^"'>]*["']?/gi, "");
  return clean;
}

function sanitizeAiOutput<T>(data: T): T {
  if (data === null || data === undefined) return data;
  if (typeof data === "string") {
    return sanitizeHtml(data) as unknown as T;
  }
  if (Array.isArray(data)) {
    return data.map(item => sanitizeAiOutput(item)) as unknown as T;
  }
  if (typeof data === "object") {
    const cleanObj: Record<string, any> = {};
    for (const key of Object.keys(data as object)) {
      cleanObj[key] = sanitizeAiOutput((data as Record<string, any>)[key]);
    }
    return cleanObj as T;
  }
  return data;
}

// Fallback Generators when API Key is not configured or fails
function getFallbackExercise(gamemode: string, data: any) {
  const count = data.count || 3;
  const vocab = data.vocab_pairs || VOCAB_POOLS[1];
  
  if (gamemode === "fill_blank") {
    return {
      questions: Array.from({ length: count }, (_, i) => {
        const item = vocab[i % vocab.length] || { term: "ubiquitous", definition: "present everywhere" };
        const optWords = [item.term, "ephemeral", "pragmatic", "verbose"];
        const optTrans = ["phổ biến khắp nơi", "ngắn hạn, tạm thời", "thực tế, thực tiễn", "dài dòng"];
        const optReasons = [
          `Chính xác! '${item.term}' có nghĩa là phổ biến khắp nơi, hoàn toàn phù hợp với ngữ cảnh mô tả sự xuất hiện rộng rãi của điện thoại thông minh.`,
          "Không phù hợp: 'ephemeral' có nghĩa là chỉ kéo dài trong thời gian ngắn hoặc tạm thời, trái ngược với xu hướng dài lâu.",
          "Không phù hợp: 'pragmatic' có nghĩa là thực tế, thiết thực trong việc giải quyết vấn đề, không mô tả tính phổ biến.",
          "Không phù hợp: 'verbose' có nghĩa là dùng quá nhiều từ ngữ không cần thiết (dài dòng)."
        ];
        return {
          sentence: `Smartphones have become _____ in modern daily life.`,
          sentence_with_blank: `Smartphones have become _____ in modern daily life.`,
          options: optWords.map((w, idx) => ({
            word: w,
            is_correct: idx === 0,
            type: idx === 0 ? "correct" : "distractor",
            reason: optReasons[idx]
          })),
          options_translations: optTrans,
          options_details: optWords.map((w, idx) => ({
            text: w,
            translation: optTrans[idx],
            is_correct: idx === 0,
            reason: optReasons[idx]
          })),
          correct_index: 0,
          explanation_vi: `Chọn '${item.term}' vì ngữ cảnh mô tả điện thoại thông minh xuất hiện ở khắp mọi nơi trong đời sống hiện đại.`,
          explanation_short: `Chọn '${item.term}' vì ngữ cảnh mô tả điện thoại thông minh xuất hiện ở khắp mọi nơi trong đời sống hiện đại.`,
          meaning_vi: `Điện thoại thông minh đã trở nên phổ biến khắp nơi trong cuộc sống hiện đại.`,
          sentence_translation: `Điện thoại thông minh đã trở nên phổ biến khắp nơi trong cuộc sống hiện đại.`,
          grammar_note: "Cấu trúc ngữ pháp: 'become + adjective' (trở nên như thế nào)."
        };
      })
    };
  }

  if (gamemode === "cloze") {
    return {
      paragraph: "In today's fast-paced world, clear communication is essential. Being [1] allows professionals to express complex ideas effectively. When teams face difficult challenges, reaching a [2] ensures everyone works toward the same goal. Having a [3] approach helps resolve conflicts quickly.",
      paragraph_with_blanks: "In today's fast-paced world, clear communication is essential. Being [1] allows professionals to express complex ideas effectively. When teams face difficult challenges, reaching a [2] ensures everyone works toward the same goal. Having a [3] approach helps resolve conflicts quickly.",
      full_solution_text: "In today's fast-paced world, clear communication is essential. Being articulate allows professionals to express complex ideas effectively. When teams face difficult challenges, reaching a consensus ensures everyone works toward the same goal. Having a pragmatic approach helps resolve conflicts quickly.",
      paragraph_full: "In today's fast-paced world, clear communication is essential. Being articulate allows professionals to express complex ideas effectively. When teams face difficult challenges, reaching a consensus ensures everyone works toward the same goal. Having a pragmatic approach helps resolve conflicts quickly.",
      story_translation: "Trong thế giới hiện đại, giao tiếp rõ ràng là rất quan trọng. Khả năng diễn đạt lưu loát giúp làm việc hiệu quả.",
      sentence_meaning: "Trong thế giới hiện đại, giao tiếp rõ ràng là rất quan trọng. Khả năng diễn đạt lưu loát giúp làm việc hiệu quả.",
      blanks: [
        {
          blank_id: 1,
          answer: "articulate",
          correct_word: "articulate",
          options: [
            { word: "articulate", is_correct: true, type: "correct", reason: "Chính xác! 'articulate' có nghĩa là diễn đạt rõ ràng." },
            { word: "verbose", is_correct: false, type: "distractor", reason: "verbose có nghĩa là dài dòng." },
            { word: "ephemeral", is_correct: false, type: "distractor", reason: "ephemeral có nghĩa là ngắn hạn." },
            { word: "ambiguous", is_correct: false, type: "distractor", reason: "ambiguous có nghĩa là mơ hồ." }
          ],
          correct_index: 0,
          meaning_vi: "diễn đạt lưu loát",
          meaning_in_vietnamese: "diễn đạt lưu loát",
          explanation_vi: "Dùng để mô tả một người có tài hùng biện hoặc diễn đạt ý kiến một cách trôi chảy, rõ ràng.",
          explanation_short: "Dùng để mô tả một người có tài hùng biện hoặc diễn đạt ý kiến một cách trôi chảy, rõ ràng."
        },
        {
          blank_id: 2,
          answer: "consensus",
          correct_word: "consensus",
          options: [
            { word: "consensus", is_correct: true, type: "correct", reason: "Chính xác! 'consensus' có nghĩa là sự đồng thuận." },
            { word: "scrutiny", is_correct: false, type: "distractor", reason: "scrutiny có nghĩa là sự xem xét kĩ lưỡng." },
            { word: "hypothesis", is_correct: false, type: "distractor", reason: "hypothesis có nghĩa là giả thuyết." },
            { word: "paradigm", is_correct: false, type: "distractor", reason: "paradigm có nghĩa là mô hình mẫu." }
          ],
          correct_index: 0,
          meaning_vi: "sự thống nhất",
          meaning_in_vietnamese: "sự thống nhất",
          explanation_vi: "consensus là sự đồng thuận hoặc nhất trí giữa các thành viên.",
          explanation_short: "consensus là sự đồng thuận hoặc nhất trí giữa các thành viên."
        },
        {
          blank_id: 3,
          answer: "pragmatic",
          correct_word: "pragmatic",
          options: [
            { word: "pragmatic", is_correct: true, type: "correct", reason: "Chính xác! 'pragmatic' có nghĩa là thực tế." },
            { word: "ambiguous", is_correct: false, type: "distractor", reason: "ambiguous có nghĩa là mơ hồ." },
            { word: "verbose", is_correct: false, type: "distractor", reason: "verbose có nghĩa là dài dòng." },
            { word: "inevitable", is_correct: false, type: "distractor", reason: "inevitable có nghĩa là không thể tránh khỏi." }
          ],
          correct_index: 0,
          meaning_vi: "thực tiễn",
          meaning_in_vietnamese: "thực tiễn",
          explanation_vi: "pragmatic là một cách tiếp cận mang tính thực tế để giải quyết các vấn đề.",
          explanation_short: "pragmatic là một cách tiếp cận mang tính thực tế để giải quyết các vấn đề."
        }
      ]
    };
  }

  if (gamemode === "translation") {
    return {
      source_sentence: "Việc sử dụng công nghệ một cách thực tế giúp cải thiện hiệu suất công việc.",
      reference_translation: "Using technology pragmatically helps improve work performance.",
      alternative_translations: [
        { text: "Applying technology in a practical way enhances productivity.", note: "Trang trọng hơn" }
      ],
      key_vocabulary: [
        { word: "pragmatically", meaning_vi: "một cách thực tế, thực tiễn", note: "Trạng từ" },
        { word: "performance", meaning_vi: "hiệu suất công việc", note: "Danh từ" }
      ],
      common_mistakes: [
        { wrong: "use technology pragmatic", correction: "use technology pragmatically", error_type: "Grammar", feedback: "Cần dùng trạng từ để bổ nghĩa cho động từ." }
      ],
      grading_rubric: "Đánh giá dựa trên độ chính xác ngữ pháp (trạng từ đứng trước động từ) và sự tự nhiên.",
      sentences: [
        {
          source_text: "Việc sử dụng công nghệ một cách thực tế giúp cải thiện hiệu suất công việc.",
          target_text: "Using technology pragmatically helps improve work performance.",
          grammar_notes: "Adv + Verb construction: 'pragmatically helps improve'"
        }
      ]
    };
  }

  if (gamemode === "unscramble") {
    const sList = [
      { correct_sentence: "Technology plays an important role in modern education.", hint: "Role of tech", translation: "Công nghệ đóng vai trò quan trọng trong giáo dục hiện đại.", sentence_meaning: "Công nghệ giúp việc học trở nên thuận tiện hơn.", key_vocab: [{ word: "education", meaning: "giáo dục" }] }
    ];
    return {
      questions: sList.map(s => ({
        correct_sentence: s.correct_sentence,
        shuffled_words: s.correct_sentence.split(" ").sort(() => Math.random() - 0.5),
        hint: s.hint,
        meaning_vi: s.translation,
        translation: s.translation,
        word_count: s.correct_sentence.split(" ").length,
        difficulty_reason: "Cấu trúc S-V-O cơ bản với cụm giới từ.",
        grammar_note: "Sử dụng cụm danh từ 'modern education' đứng sau giới từ 'in'.",
        key_vocabulary: s.key_vocab.map(k => ({ word: k.word, meaning_vi: k.meaning }))
      }))
    };
  }

  if (gamemode === "story") {
    return {
      story: {
        title: "Alex's Persuasive Speech",
        content: "Alex was known for his articulate presentation style. During the annual conference, he presented a comprehensive plan to mitigate operational risks. Despite initial skepticism from the board, his persuasive arguments helped the team reach a unanimous consensus on the new strategic paradigm.",
        highlighted_vocab: [
          { word: "articulate", meaning_vi: "diễn đạt trôi chảy, rõ ràng", context_meaning: "Cách nói rõ ràng và thu hút người nghe" }
        ],
        full_translation: "Alex nổi tiếng với phong cách thuyết trình diễn đạt lưu loát và rõ ràng."
      },
      questions: [
        {
          question: "What was Alex known for during presentations?",
          options: [
            { text: "His articulate style", is_correct: true },
            { text: "His verbose explanations", is_correct: false },
            { text: "His ambiguous slides", is_correct: false },
            { text: "His hesitant tone", is_correct: false }
          ],
          explanation: "Alex nổi tiếng với phong cách thuyết trình diễn đạt lưu loát và rõ ràng (articulate presentation style).",
          evidence_quote: "Alex was known for his articulate presentation style.",
          type: "Detail"
        }
      ],
      discussion_prompt: "Thảo luận về tầm quan trọng của việc thuyết trình rõ ràng trong công việc.",
      comprehension_questions: [
        {
          question: "What was Alex known for during presentations?",
          options: ["His articulate style", "His verbose explanations", "His ambiguous slides", "His hesitant tone"],
          correct_index: 0,
          explanation: "Alex nổi tiếng với phong cách thuyết trình diễn đạt lưu loát và rõ ràng (articulate presentation style).",
          quote_evidence: "Alex was known for his articulate presentation style."
        }
      ]
    };
  }

  if (gamemode === "sentence_transform") {
    return {
      questions: [
        {
          original: "They built the new bridge in less than six months.",
          original_sentence: "They built the new bridge in less than six months.",
          prompt: "Rewrite using the passive voice (start with 'The new bridge...').",
          instruction: "Rewrite using the passive voice (start with 'The new bridge...').",
          expected_answer: "The new bridge was built in less than six months.",
          normalized_answer: "the new bridge was built in less than six months",
          grammar_rule: "Passive voice in Simple Past: Subject + was/were + Past Participle",
          acceptable_variations: [
            { text: "The new bridge was built in under six months.", note: "Sử dụng under thay cho less than" }
          ],
          common_errors: [
            { error: "The new bridge is built in less than six months.", feedback: "Sai thì: câu gốc dùng 'built' ở quá khứ đơn, nên câu bị động phải dùng 'was built'." }
          ]
        }
      ]
    };
  }

  if (gamemode === "taboo") {
    return {
      rounds: [
        {
          target_word: "UBIQUITOUS",
          secret_word: "UBIQUITOUS",
          taboo_words: ["EVERYWHERE", "COMMON", "FOUND", "PRESENT", "ALWAYS"],
          forbidden_words: ["EVERYWHERE", "COMMON", "FOUND", "PRESENT", "ALWAYS"],
          clue: "Describing something that seems to exist in all places at the same time, like modern technology or mobile phones.",
          ai_description: "Describing something that seems to exist in all places at the same time, like modern technology or mobile phones.",
          meaning_vi: "Phổ biến khắp nơi",
          sample_acceptable_phrases: ["present in all places", "found everywhere"],
          sample_forbidden_phrases: ["always common everywhere"]
        }
      ]
    };
  }

  return { questions: [] };
}

// Main handler for Bridge JS requests
app.post("/api/bridge", async (req, res) => {
  const { action, data = {} } = req.body || {};

  try {
    if (action === "list_decks") {
      return res.json({
        success: true,
        data: { decks: BUILTIN_DECKS }
      });
    }

    if (action === "get_source_models") {
      return res.json({
        success: true,
        data: { models: [{ id: 101, name: "Vocabulary Note (Term & Definition)" }] }
      });
    }

    if (action === "get_source_fields") {
      return res.json({
        success: true,
        data: { fields: ["Term", "Definition"] }
      });
    }

    if (action === "sample_vocab_pairs") {
      const deckId = Number(data.deck_id) || 1;
      const limit = Math.min(Number(data.limit) || 50, 50);
      const pairs = VOCAB_POOLS[deckId] || VOCAB_POOLS[1];
      const shuffledDeck = shuffleArray(pairs);
      const selected = shuffledDeck.slice(0, limit);
      return res.json({
        success: true,
        data: {
          pairs: selected,
          total: selected.length,
          limit: limit,
          exhausted: false
        }
      });
    }

    if (action === "get_settings") {
      return res.json({
        success: true,
        data: appSettings
      });
    }

    if (action === "save_settings") {
      Object.assign(appSettings, data);
      return res.json({
        success: true,
        data: { saved: Object.keys(data) }
      });
    }

    if (action === "get_ui_lang") {
      return res.json({
        success: true,
        data: { lang: appSettings.ui_lang || "vi" }
      });
    }

    if (action === "set_ui_lang") {
      appSettings.ui_lang = data.lang || "vi";
      return res.json({
        success: true,
        data: { lang: appSettings.ui_lang }
      });
    }

    if (action === "get_ui_strings") {
      const lang = appSettings.ui_lang || "vi";
      const filePath = path.join(process.cwd(), "lang", `${lang}.json`);
      let strings = {};
      if (fs.existsSync(filePath)) {
        strings = JSON.parse(fs.readFileSync(filePath, "utf-8"));
      } else {
        const enPath = path.join(process.cwd(), "lang", "en.json");
        if (fs.existsSync(enPath)) {
          strings = JSON.parse(fs.readFileSync(enPath, "utf-8"));
        }
      }
      return res.json({
        success: true,
        data: { strings, lang }
      });
    }

    if (action === "check_api_key") {
      const hasKey = Boolean(process.env.GEMINI_API_KEY);
      return res.json({
        success: true,
        data: {
          has_key: hasKey,
          key_count: hasKey ? 1 : 0,
          keys: hasKey ? ["Gemini API Key"] : []
        }
      });
    }

    if (action === "test_key" || action === "test_all_keys") {
      const ai = getAiClient();
      if (!ai) {
        return res.json({
          success: true,
          data: {
            results: [{ key: 1, ok: false, error: "GEMINI_API_KEY environment variable not configured." }]
          }
        });
      }
      try {
        const response = await ai.models.generateContent({
          model: "gemini-2.5-flash",
          contents: "Hello, reply 'OK'",
        });
        return res.json({
          success: true,
          data: {
            results: [{ key: 1, ok: true, model: "gemini-2.5-flash", response: response.text }]
          }
        });
      } catch (err: any) {
        return res.json({
          success: true,
          data: {
            results: [{ key: 1, ok: false, error: err.message || "Failed API key test" }]
          }
        });
      }
    }

    if (action === "save_context") {
      appContext = data;
      return res.json({ success: true, data: {} });
    }

    if (action === "load_context") {
      return res.json({
        success: true,
        data: appContext ? { has_context: true, ...appContext } : { has_context: false }
      });
    }

    if (action === "clear_context") {
      appContext = null;
      return res.json({ success: true, data: { success: true } });
    }

    if (action === "save_to_anki") {
      return res.json({ success: true, data: { success: true, count: 1 } });
    }

    if (action === "close_hub") {
      return res.json({ success: true, data: {} });
    }

    if (action === "generate") {
      const gamemode = data.gamemode || "fill_blank";
      const rawCount = Number(data.count) || 5;
      const count = Math.max(1, Math.min(rawCount, 15)); // Clamp between 1 and 15
      const language = String(data.language || "en").substring(0, 20);
      const level = String(data.level || "intermediate").substring(0, 30);
      const topic = String(data.topic || "daily_life").substring(0, 100);
      const vocabPairs = Array.isArray(data.vocab_pairs) ? data.vocab_pairs : [];

      // Game Mode 5: Word Matching is offline logic
      if (gamemode === "matching") {
        const rawPairs = vocabPairs.length > 0 
          ? vocabPairs.map((p: any) => ({ term: p.term || p.word || "", definition: p.definition || p.meaning || "" }))
          : VOCAB_POOLS[1].slice(0, count).map(p => ({ term: p.term, definition: p.definition }));
        
        const pairs = rawPairs.map((p: any, idx: number) => ({
          id: `p_${Math.random().toString(36).substring(2, 9)}_${idx}`,
          term: p.term,
          definition: p.definition
        }));

        return res.json({
          success: true,
          data: {
            error: false,
            pairs
          }
        });
      }

      // Check Gemini API
      const ai = getAiClient();
      if (!ai) {
        console.warn(`[Server] GEMINI_API_KEY missing - returning rich fallback exercise for ${gamemode}`);
        let fallback = getFallbackExercise(gamemode, data);
        if (gamemode === "unscramble" && fallback.sentences) {
          fallback = {
            questions: fallback.sentences.map((s: any) => ({
              correct_sentence: s.correct_sentence,
              shuffled_words: s.correct_sentence.split(" ").sort(() => Math.random() - 0.5),
              hint: s.hint,
              translation: s.translation,
              word_count: s.correct_sentence.split(" ").length
            }))
          };
        }
        return res.json({
          success: true,
          data: {
            ...fallback,
            is_fallback: true,
            fallback_reason: "Chưa cấu hình GEMINI_API_KEY. Đang sử dụng bài tập mẫu."
          }
        });
      }

      // Generate via Gemini API
      try {
        // Candidate pool: up to 50 terms
        const candidatePool = (vocabPairs && vocabPairs.length > 0)
          ? vocabPairs.slice(0, 50)
          : (VOCAB_POOLS[1] || []).slice(0, 50);

        // Mathematical random selection: Fisher-Yates shuffle
        const shuffledPool = shuffleArray(candidatePool);
        // Sample 5 to 10 random terms
        const sampleSize = Math.min(
          shuffledPool.length,
          Math.floor(Math.random() * 6) + 5
        );
        const vocabSample = shuffledPool.slice(0, sampleSize);

        const vocabSection = vocabSample.length > 0
          ? `Mandatory vocabulary terms to feature (randomly selected ${vocabSample.length} terms): ${vocabSample.map((p: any) => `${p.term} (${p.definition})`).join("; ")}`
          : "None";

        const prompt = `<task>
Generate a high-quality '${gamemode}' language exercise.
Target Language: ${language}
Level: ${level}
Topic: ${topic}
Count: ${count}
${gamemode === "cloze" ? `Blanks Count: ${data.num_blanks || 5}` : ""}
</task>

<context>
${vocabSection}
</context>

<language_constraints>
- TARGET LANGUAGE (${language}): Used EXCLUSIVELY for raw exercise content (sentences, reading passages, blank options, secret words).
- SUPPORT LANGUAGE (Tiếng Việt): Used EXCLUSIVELY for ALL keys ending with '_vietnamese' (explanations, translations, hints). NEVER output ${language} in these fields.
</language_constraints>

<example_output_format>
Here is an example of the STRICT bilingual format expected (for fill_blank):
{
  "sentence_with_blank": "If you want to see your family, you can make a _____.",
  "full_sentence": "If you want to see your family, you can make a video call.",
  "blank_word": "video call",
  "options": ["video call", "video game", "video clip", "video player"],
  "options_vietnamese": ["cuộc gọi video", "trò chơi điện tử", "đoạn video ngắn", "đầu phát video"],
  "correct_index": 0,
  "sentence_vietnamese": "Nếu bạn muốn gặp gia đình mình, bạn có thể thực hiện một cuộc gọi video.",
  "explanation_vietnamese": "Chọn 'video call' (cuộc gọi video) vì nó phù hợp nhất với ngữ cảnh muốn liên lạc và nhìn thấy người thân ở xa."
}
</example_output_format>

<schema_requirements>
Generate exactly ${count} items following the exact JSON schema provided in the API configuration. Ensure EVERY single field ending with '_vietnamese' is populated in fluent Vietnamese without leaving any field blank or falling back to ${language}.
</schema_requirements>`;

        const schema = SCHEMAS[gamemode];

        const response = await ai.models.generateContent({
          model: "gemini-3.6-flash",
          contents: prompt,
          config: schema ? {
            systemInstruction: `You are an elite AI language educator designed for Vietnamese learners. 
Your primary directive is STRICT BILINGUAL SEPARATION. You must seamlessly switch between the TARGET LANGUAGE (${language}) and the SUPPORT LANGUAGE (Vietnamese).

CRITICAL RULES FOR JSON OUTPUT:
1. THE TARGET LANGUAGE ONLY RULE: Fields containing raw exercise content (sentences, reading passages, blank options, secret words) MUST be 100% in the target language (${language}).
2. THE VIETNAMESE ONLY RULE: Fields requiring explanation, translation, hints, grammar notes, or word meanings (all keys ending with _vietnamese) MUST be 100% in natural, fluent Vietnamese (Tiếng Việt). NEVER output ${language} or English in _vietnamese fields.
3. EXPLANATION QUALITY: When explaining "WHY" an option is correct (explanation_vietnamese), clearly cite the grammar rule, vocabulary context, or collocation IN VIETNAMESE.
4. STRUCTURAL INTEGRITY: Output NOTHING but valid JSON. No markdown backticks (\`\`\`json), no conversational filler.`,
            temperature: 0.2,
            maxOutputTokens: 3000,
            responseMimeType: "application/json",
            responseSchema: schema
          } : undefined
        });

        let parsed: any = {};
        try {
          parsed = JSON.parse(response.text || "{}");
        } catch (_) {
          parsed = getFallbackExercise(gamemode, data);
        }

        // Sanitize AI Output to prevent XSS script tags and inline handlers
        parsed = sanitizeAiOutput(parsed);

        // Post-process & normalize _vietnamese keys for client UI compatibility
        if (parsed) {
          if (gamemode === "fill_blank" && parsed.questions) {
            parsed.questions = parsed.questions.map((q: any) => {
              const rawOpts = q.options || [];
              const opts = rawOpts.map((o: any) => typeof o === 'object' ? (o.text || o.word || String(o)) : String(o));
              const trans = q.options_vietnamese || q.options_translations || [];
              let details = Array.isArray(q.options_details) ? q.options_details : [];

              if (!details.length && opts.length) {
                details = opts.map((optText: string, idx: number) => {
                  const isCorrect = idx === q.correct_index;
                  const tr = trans[idx] || (typeof rawOpts[idx] === 'object' ? rawOpts[idx].translation : '');
                  const reason = isCorrect
                    ? (q.explanation_vietnamese || q.explanation_short || `Từ '${optText}' phù hợp với ngữ cảnh câu.`)
                    : `Không phù hợp: Từ '${optText}' ${tr ? `(${tr})` : ''} không chính xác trong ngữ cảnh này.`;
                  return {
                    text: optText,
                    translation: tr,
                    is_correct: isCorrect,
                    reason: reason
                  };
                });
              }

              return {
                ...q,
                options: opts,
                options_translations: trans,
                options_details: details,
                sentence_translation: q.sentence_vietnamese || q.full_sentence_translation || q.sentence_translation || "",
                explanation_short: q.explanation_vietnamese || q.explanation_short || "",
                grammar_note: q.grammar_note_vietnamese || q.grammar_note || ""
              };
            });
          } else if (gamemode === "cloze") {
            if (parsed.sentence_meaning_vietnamese || parsed.sentence_vietnamese) {
              parsed.sentence_meaning = parsed.sentence_meaning_vietnamese || parsed.sentence_vietnamese || parsed.sentence_meaning || "";
            }
            if (parsed.blanks) {
              parsed.blanks = parsed.blanks.map((b: any) => ({
                ...b,
                meaning_in_vietnamese: b.meaning_vietnamese || b.meaning_in_vietnamese || "",
                explanation_short: b.explanation_vietnamese || b.explanation_short || ""
              }));
            }
          } else if (gamemode === "story") {
            if (parsed.passage_vietnamese) {
              parsed.passage_translation = parsed.passage_vietnamese;
            }
            if (parsed.comprehension_questions) {
              parsed.comprehension_questions = parsed.comprehension_questions.map((q: any) => ({
                ...q,
                options_translations: q.options_vietnamese || q.options_translations || [],
                explanation: q.explanation_vietnamese || q.explanation || ""
              }));
            }
          } else if (gamemode === "translation" && parsed.sentences) {
            parsed.sentences = parsed.sentences.map((s: any) => ({
              ...s,
              target_text: s.target_text_vietnamese || s.target_text || "",
              grammar_notes: s.grammar_notes_vietnamese || s.grammar_notes || ""
            }));
          } else if (gamemode === "unscramble" && parsed.sentences) {
            parsed = {
              questions: parsed.sentences.map((s: any) => {
                const hint = s.hint_vietnamese || s.hint || "";
                const translation = s.translation_vietnamese || s.translation || "";
                return {
                  correct_sentence: s.correct_sentence,
                  shuffled_words: s.correct_sentence.split(" ").sort(() => Math.random() - 0.5),
                  hint: hint,
                  translation: translation,
                  sentence_meaning: s.sentence_meaning_vietnamese || s.sentence_meaning || translation,
                  key_vocab: (s.key_vocab || []).map((v: any) => ({
                    word: v.word,
                    meaning: v.meaning_vietnamese || v.meaning || ""
                  })),
                  word_count: s.correct_sentence.split(" ").length
                };
              })
            };
          } else if (gamemode === "sentence_transform" && parsed.questions) {
            parsed.questions = parsed.questions.map((q: any) => ({
              ...q,
              instruction: q.instruction_vietnamese || q.instruction || "",
              grammar_rule: q.grammar_rule_vietnamese || q.grammar_rule || ""
            }));
          } else if (gamemode === "taboo" && parsed.rounds) {
            parsed.rounds = parsed.rounds.map((r: any) => ({
              ...r,
              word_meaning_vietnamese: r.word_meaning_vietnamese || r.meaning_vietnamese || ""
            }));
          }
        }

        return res.json({
          success: true,
          data: parsed
        });
      } catch (err: any) {
        console.error(`[Server] Gemini API error for ${gamemode}:`, err);
        const fallback = getFallbackExercise(gamemode, data);
        const isQuotaError = err?.status === 429 || String(err?.message || "").includes("429") || String(err?.message || "").includes("quota");
        const reasonMsg = isQuotaError
          ? "Đã vượt quá hạn ngạch AI (429 Rate Limit). Đang tự động chuyển sang bài tập mẫu."
          : "Lỗi kết nối Gemini AI. Đang tự động chuyển sang bài tập mẫu.";
        return res.json({
          success: true,
          data: {
            ...fallback,
            is_fallback: true,
            fallback_reason: reasonMsg
          }
        });
      }
    }

    if (action === "ai_grade") {
      const { gamemode, user_answer, expected, secret_word } = data;
      const targetAns = expected || secret_word || "";

      // Normalize text helper: lowercase, NFKD unicode normalization, strip trailing punctuation, strip extra whitespace
      const normalizeText = (text: string): string => {
        if (!text) return "";
        return String(text)
          .trim()
          .toLowerCase()
          .normalize("NFKD")
          .replace(/[.,!?;:]$/, "")
          .replace(/\s+/g, " ");
      };

      const uNorm = normalizeText(user_answer);
      const tNorm = normalizeText(targetAns);
      const isExactMatch = uNorm.length > 0 && uNorm === tNorm;

      const ai = getAiClient();

      if (!ai || isExactMatch) {
        const isCorrect = isExactMatch || (tNorm.length > 0 && (uNorm.includes(tNorm) || tNorm.includes(uNorm)));

        return res.json({
          success: true,
          data: {
            correct: isCorrect,
            score: isExactMatch ? 100 : (isCorrect ? 85 : 40),
            explanation: isExactMatch
              ? "Xuất sắc! Câu trả lời hoàn toàn chính xác."
              : isCorrect
                ? `Khá tốt! Đáp án chính xác gợi ý: '${targetAns}'`
                : `Cần cải thiện. Đáp án chính xác: '${targetAns}'`
          }
        });
      }

      try {
        const prompt = `Evaluate student response for exercise type '${gamemode}':
Target/Expected Answer: "${targetAns}"
Student Answer: "${user_answer}"

Rules:
- Be flexible with minor punctuation or capitalization variations.
- Assess accuracy, grammar, vocabulary fit, and natural expression.
- Provide encouraging, clear, concise feedback in Vietnamese.`;

        const response = await ai.models.generateContent({
          model: "gemini-3.6-flash",
          contents: prompt,
          config: {
            systemInstruction: "You are an encouraging AI language teacher grading a student's answer. Return a strict JSON response with exact keys.",
            temperature: 0.2,
            maxOutputTokens: 600,
            responseMimeType: "application/json",
            responseSchema: {
              type: "object",
              properties: {
                correct: { type: "boolean" },
                score: { type: "integer" },
                explanation: { type: "string" }
              },
              required: ["correct", "score", "explanation"]
            }
          }
        });

        let result = {};
        try {
          result = JSON.parse(response.text || "{}");
        } catch (_) {
          result = { correct: true, score: 90, explanation: "Đã nhận và lưu câu trả lời." };
        }

        result = sanitizeAiOutput(result);

        return res.json({
          success: true,
          data: result
        });
      } catch (err: any) {
        console.error("[Server] Error during ai_grade:", err?.message || err);
        const isPartial = tNorm.length > 0 && (uNorm.includes(tNorm) || tNorm.includes(uNorm));
        return res.json({
          success: true,
          data: {
            correct: isPartial,
            score: isPartial ? 80 : 40,
            explanation: isPartial
              ? `Câu trả lời khá sát. Đáp án gợi ý: '${targetAns}'`
              : `Đáp án gợi ý: '${targetAns}'`
          }
        });
      }
    }

    return res.json({
      success: false,
      data: {},
      error_code: "E_UNKNOWN_ACTION",
      message: `Unknown bridge action: ${action}`
    });
  } catch (error: any) {
    console.error("[Server] Exception in /api/bridge:", error);
    return res.json({
      success: false,
      data: {},
      error_code: "E_SERVER_ERROR",
      message: error.message || "Internal server error"
    });
  }
});

// Serve static web interface
const webDir = path.join(process.cwd(), "web");
app.use(express.static(webDir));

// Fallback to index.html for root or SPA paths
app.use((req, res) => {
  res.sendFile(path.join(webDir, "index.html"));
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`AI Learning Hub server running at http://0.0.0.0:${PORT}`);
});
