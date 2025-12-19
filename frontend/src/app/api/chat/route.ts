import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';
import { backendApi } from '@/lib/backend-api';
import { TradeNameRegistrationAgent } from '@/lib/trade-name-agent';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Global agent instance to maintain state across requests
// In production, this should be stored in session/database
const globalAgents = new Map<string, TradeNameRegistrationAgent>();

function getOrCreateAgent(sessionId: string = 'default'): TradeNameRegistrationAgent {
  if (!globalAgents.has(sessionId)) {
    console.log('🆕 Creating new agent for session:', sessionId);
    globalAgents.set(sessionId, new TradeNameRegistrationAgent(process.env.OPENAI_API_KEY!));
  }
  return globalAgents.get(sessionId)!;
}

function resetAgentSession(sessionId: string): void {
  console.log('🔄 Resetting agent session:', sessionId);
  if (globalAgents.has(sessionId)) {
    globalAgents.delete(sessionId);
  }
}

const GENERAL_ASSISTANT_PROMPT = `You are a knowledgeable bilingual assistant for UAE business services and government procedures. You provide helpful information in both English and Arabic about:

ENGLISH:
• UAE business setup and licensing procedures
• DED (Department of Economic Development) services
• General business registration guidance
• Company formation requirements
• Documentation and legal requirements

ARABIC:
• إجراءات إعداد الأعمال والترخيص في دولة الإمارات
• خدمات دائرة التنمية الاقتصادية
• إرشادات تسجيل الأعمال العامة
• متطلبات تكوين الشركات
• متطلبات التوثيق والمتطلبات القانونية

IMPORTANT GUIDELINES:
- Always provide responses in both English and Arabic in separate paragraphs
- For specific trade name registration requests, redirect users to the trade name specialist
- Provide accurate, up-to-date information about UAE business procedures
- Be helpful, professional, and concise
- If users want to check or register specific trade names, say: 

"I'll connect you with our trade name registration specialist for that.

سأصلك بمتخصص تسجيل الأسماء التجارية لذلك."

You complement the specialized trade name registration system with general business knowledge.`;

export async function POST(request: NextRequest) {
  try {
    const { message, messages = [], sessionId = 'default' } = await request.json();

    console.log('🔍 Chat API Request:', { 
      message, 
      sessionId, 
      messagesCount: messages.length,
      existingAgents: Array.from(globalAgents.keys())
    });

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    // Get or create trade name registration agent for this session
    const tradeNameAgent = getOrCreateAgent(sessionId);
    
    console.log('📊 Agent state before processing:', {
      sessionId,
      agentStatus: tradeNameAgent.getRegistrationStatus(),
      isNewAgent: !globalAgents.has(sessionId)
    });

    // Enhanced trade name detection logic
    const lowerMessage = message.toLowerCase();
    const isTradeNameQuery = 
      // Direct trade name keywords
      lowerMessage.includes('trade name') ||
      lowerMessage.includes('business name') ||
      lowerMessage.includes('company name') ||
      lowerMessage.includes('register') ||
      lowerMessage.includes('check name') ||
      lowerMessage.includes('name available') ||
      lowerMessage.includes('availability') ||
      // Business entity types
      lowerMessage.includes('llc') ||
      lowerMessage.includes('establishment') ||
      lowerMessage.includes('partnership') ||
      lowerMessage.includes('est ') ||
      // PRO services
      lowerMessage.includes('pro service') ||
      lowerMessage.includes('pro officer') ||
      // Registration intents
      lowerMessage.includes('start business') ||
      lowerMessage.includes('open company') ||
      lowerMessage.includes('new business') ||
      lowerMessage.includes('business license') ||
      // Simple yes/no responses (when agent is active)
      (tradeNameAgent.getRegistrationStatus().stage !== 'greeting' && (
        lowerMessage.includes('yes') ||
        lowerMessage.includes('no') ||
        lowerMessage === 'y' ||
        lowerMessage === 'n'
      )) ||
      // Common business names patterns (contains business-like terms)
      (/\b(solutions?|services?|trading|technologies?|tech|digital|consulting|group|international|global|company|corp|limited)\b/i.test(message) &&
       message.split(' ').length <= 6) ||
      // If agent is already in progress (any stage except greeting)
      tradeNameAgent.getRegistrationStatus().stage !== 'greeting';

    if (isTradeNameQuery) {
      // Use specialized trade name registration agent (no OpenAI needed)
      const agentResponse = await tradeNameAgent.processMessage(message);
      
      return NextResponse.json({
        message: {
          role: 'assistant',
          content: agentResponse,
          timestamp: new Date().toISOString(),
        },
        agentType: 'trade_name_registration',
        registrationStatus: tradeNameAgent.getRegistrationStatus(),
      });
    }

    // For non-trade-name queries, check if OpenAI key is available
    if (!process.env.OPENAI_API_KEY || process.env.OPENAI_API_KEY === 'your_openai_api_key_here') {
      // Enhanced bilingual fallback response when OpenAI is not configured
      const fallbackResponse = `🏢 **Welcome to UAE Business Services!**

🏢 **مرحباً بك في خدمات الأعمال الإماراتية!**

I'm your specialized assistant for UAE trade name registration and business setup.

أنا مساعدك المتخصص في تسجيل الأسماء التجارية وإعداد الأعمال في دولة الإمارات.

**🎯 What I can help you with:**
• **Trade Name Registration** - Check availability and register business names
• **Entity Type Selection** - Choose between EST, LLC, or Partnership
• **PRO Services** - Professional assistance with government procedures
• **Arabic Transliteration** - Official Arabic names for your business
• **Government Compliance** - Ensure your name meets DED requirements

**🎯 ما يمكنني مساعدتك فيه:**
• **تسجيل الاسم التجاري** - فحص التوفر وتسجيل أسماء الأعمال
• **اختيار نوع الكيان** - الاختيار بين EST أو LLC أو الشراكة
• **خدمات PRO** - المساعدة المهنية في الإجراءات الحكومية
• **النقل الحرفي العربي** - أسماء عربية رسمية لعملك
• **الامتثال الحكومي** - تأكد من أن اسمك يلبي متطلبات دائرة التنمية الاقتصادية

**🚀 Quick Start Examples:**
- "I want to register Amazing Tech Solutions LLC"
- "Check if Digital Trading EST is available"
- "Help me start a consulting business"
- "Register Best Services Partnership"

**🚀 أمثلة البداية السريعة:**
- "أريد تسجيل Amazing Tech Solutions LLC"
- "تحقق من توفر Digital Trading EST"
- "ساعدني في بدء عمل استشاري"
- "سجل Best Services Partnership"

**💬 For General Business Questions:**
I can also help with UAE business setup procedures, DED requirements, and company formation guidance.

**💬 للأسئلة التجارية العامة:**
يمكنني أيضاً المساعدة في إجراءات إعداد الأعمال الإماراتية ومتطلبات دائرة التنمية الاقتصادية وإرشادات تكوين الشركات.

How can I assist you with your business registration today?

كيف يمكنني مساعدتك في تسجيل عملك اليوم؟`;

      return NextResponse.json({
        message: {
          role: 'assistant',
          content: fallbackResponse,
          timestamp: new Date().toISOString(),
        },
        agentType: 'enhanced_bilingual_fallback',
        note: 'Full trade name registration available - OpenAI optional for general queries'
      });
    }

    // For non-trade-name queries, use general OpenAI assistant
    const openaiMessages = [
      {
        role: 'system' as const,
        content: GENERAL_ASSISTANT_PROMPT
      },
      ...messages.map((msg: { role: string; content: string }) => ({
        role: msg.role,
        content: msg.content
      })),
      {
        role: 'user' as const,
        content: message
      }
    ];

    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: openaiMessages,
      temperature: 0.7,
      max_tokens: 800,
    });

    const assistantMessage = completion.choices[0]?.message?.content;

    if (!assistantMessage) {
      throw new Error('No response from OpenAI');
    }

    return NextResponse.json({
      message: {
        role: 'assistant',
        content: assistantMessage,
        timestamp: new Date().toISOString(),
      },
      usage: completion.usage,
      agentType: 'general_assistant',
    });

  } catch (error) {
    console.error('Chat API error:', error);
    
    // If it's an OpenAI API error, provide helpful message
    if (error instanceof Error && error.message.includes('invalid_api_key')) {
      return NextResponse.json({
        message: {
          role: 'assistant',
          content: `🏢 **UAE Business Services - Trade Name Registration Available!**

🏢 **خدمات الأعمال الإماراتية - تسجيل الاسم التجاري متاح!**

Even without OpenAI configuration, I can fully assist you with:

حتى بدون إعداد OpenAI، يمكنني مساعدتك بالكامل في:

**✅ Complete Trade Name Registration:**
- Real-time availability checking
- Prohibited words validation
- Similar names detection
- Arabic transliteration
- Government compliance verification

**✅ تسجيل الاسم التجاري الكامل:**
- فحص التوفر في الوقت الفعلي
- التحقق من الكلمات المحظورة
- اكتشاف الأسماء المشابهة
- النقل الحرفي العربي
- التحقق من الامتثال الحكومي

**🚀 Try These Examples:**
- "I want to register Innovation Tech Solutions LLC"
- "Check availability of Smart Trading EST"
- "Help me register Digital Services Partnership"

**🚀 جرب هذه الأمثلة:**
- "أريد تسجيل Innovation Tech Solutions LLC"
- "تحقق من توفر Smart Trading EST"
- "ساعدني في تسجيل Digital Services Partnership"

**🔧 For Enhanced General Assistance:**
Configure your OpenAI API key in \`.env.local\` to enable general business consultation features.

**🔧 للمساعدة العامة المحسنة:**
قم بإعداد مفتاح OpenAI API في \`.env.local\` لتمكين ميزات الاستشارة التجارية العامة.

**Ready to start your business registration?**

**مستعد لبدء تسجيل عملك؟**`,
          timestamp: new Date().toISOString(),
        },
        agentType: 'error_enhanced_bilingual_fallback',
      });
    }

    return NextResponse.json(
      { error: 'Failed to get response from AI' },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { sessionId } = await request.json();
    
    if (!sessionId) {
      return NextResponse.json({ error: 'Session ID is required' }, { status: 400 });
    }

    resetAgentSession(sessionId);
    
    return NextResponse.json({
      success: true,
      message: 'Session reset successfully',
      sessionId
    });
  } catch (error) {
    console.error('Session reset error:', error);
    return NextResponse.json(
      { error: 'Failed to reset session' },
      { status: 500 }
    );
  }
} 