"use client";

import { useState } from "react";
import { useRouter } from 'next/navigation';
import { Sidebar } from '@/components/ui/sidebar';
import { 
  Building2, 
  FileText, 
  CreditCard, 
  CheckCircle, 
  AlertCircle, 
  Info,
  HelpCircle,
  Globe,
  Phone,
  Mail,
  Clock,
  DollarSign,
  Users,
  Shield,
  Download,
  Upload,
  Search,
  MessageCircle
} from "lucide-react";

const HelpSection = ({ 
  icon: Icon, 
  title, 
  titleAr, 
  children, 
  variant = "default" 
}: { 
  icon: any, 
  title: string, 
  titleAr: string, 
  children: React.ReactNode, 
  variant?: "default" | "warning" | "success"
}) => (
  <div className="mb-8">
    <div className="flex items-center gap-3 mb-4">
      <Icon className={`h-6 w-6 ${variant === "warning" ? "text-yellow-600" : variant === "success" ? "text-green-600" : "text-blue-600"}`} />
      <div className="flex flex-col">
        <h2 className="text-xl font-bold text-foreground">{title}</h2>
        <p className="text-sm text-muted-foreground font-normal" dir="rtl">{titleAr}</p>
      </div>
    </div>
    <div className="ml-9">
      {children}
    </div>
    <hr className="mt-6 border-border" />
  </div>
);

const ProcessStep = ({ 
  step, 
  title, 
  titleAr, 
  description, 
  descriptionAr, 
  icon: Icon,
  status = "pending"
}: {
  step: number,
  title: string,
  titleAr: string,
  description: string,
  descriptionAr: string,
  icon: any,
  status?: "pending" | "active" | "completed"
}) => (
  <div className="flex items-start gap-4 p-4 rounded-lg bg-muted/30">
    <div className={`flex items-center justify-center w-8 h-8 rounded-full ${
      status === "completed" ? "bg-green-100 text-green-700" :
      status === "active" ? "bg-blue-100 text-blue-700" :
      "bg-gray-100 text-gray-600"
    }`}>
      <span className="text-sm font-bold">{step}</span>
    </div>
    <div className="flex-1 space-y-2">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-muted-foreground" />
        <h4 className="font-medium">{title}</h4>
      </div>
      <p className="text-sm text-muted-foreground" dir="rtl">{titleAr}</p>
      <p className="text-sm">{description}</p>
      <p className="text-sm text-muted-foreground" dir="rtl">{descriptionAr}</p>
    </div>
  </div>
);

const FAQItem = ({ 
  question, 
  questionAr, 
  answer, 
  answerAr 
}: {
  question: string,
  questionAr: string,
  answer: string,
  answerAr: string
}) => {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className="py-3">
      <button
        className="w-full p-3 text-left hover:bg-muted/30 transition-colors rounded-md"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="font-medium">{question}</p>
            <p className="text-sm text-muted-foreground" dir="rtl">{questionAr}</p>
          </div>
          <HelpCircle className={`h-4 w-4 transition-transform ${isOpen ? "rotate-180" : ""}`} />
        </div>
      </button>
      {isOpen && (
        <div className="px-3 pb-3 space-y-2">
          <hr className="mb-3 opacity-50" />
          <p className="text-sm">{answer}</p>
          <p className="text-sm text-muted-foreground" dir="rtl">{answerAr}</p>
        </div>
      )}
    </div>
  );
};

export default function HelpPage() {
  const router = useRouter();

  const handleNavigation = (path: string) => {
    router.push(path);
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar currentPage="help" />
      
      <div className="flex-1 flex flex-col ml-[3.05rem]">
        {/* Header */}
        <div className="border-b border-border p-4">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-3xl font-bold text-foreground mb-2">
              Trade License Help Center
            </h1>
            <p className="text-lg text-muted-foreground mb-1">
              Complete guide for UAE Trade License application process
            </p>
            <p className="text-sm text-muted-foreground" dir="rtl">
              دليل شامل لعملية طلب الترخيص التجاري في دولة الإمارات العربية المتحدة
            </p>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-4xl mx-auto space-y-2">
                
            {/* Overview Section */}
            <HelpSection icon={Building2} title="System Overview" titleAr="نظرة عامة على النظام">
              <div className="space-y-4">
                <p>
                  Our AI-powered trade license system guides you through the complete process of obtaining a 
                  UAE commercial trade license in Abu Dhabi. The system integrates with official UAE DED APIs 
                  to provide real-time validation and processing.
                </p>
                <p dir="rtl" className="text-muted-foreground">
                  نظامنا المدعوم بالذكاء الاصطناعي يرشدك خلال العملية الكاملة للحصول على ترخيص تجاري 
                  تجاري في أبو ظبي. يتكامل النظام مع واجهات برمجة التطبيقات الرسمية لدائرة التنمية الاقتصادية 
                  لتوفير التحقق والمعالجة في الوقت الفعلي.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                  <div className="p-4 bg-muted/20 rounded-lg">
                    <MessageCircle className="h-8 w-8 text-blue-600 mb-2" />
                    <h4 className="font-medium">AI Chat Assistant</h4>
                    <p className="text-sm text-muted-foreground">مساعد المحادثة بالذكاء الاصطناعي</p>
                  </div>
                  <div className="p-4 bg-muted/20 rounded-lg">
                    <Shield className="h-8 w-8 text-green-600 mb-2" />
                    <h4 className="font-medium">Official UAE Integration</h4>
                    <p className="text-sm text-muted-foreground">التكامل الرسمي مع الإمارات</p>
                  </div>
                  <div className="p-4 bg-muted/20 rounded-lg">
                    <CheckCircle className="h-8 w-8 text-purple-600 mb-2" />
                    <h4 className="font-medium">Real-time Validation</h4>
                    <p className="text-sm text-muted-foreground">التحقق في الوقت الفعلي</p>
                  </div>
                </div>
              </div>
            </HelpSection>

            {/* Application Process */}
            <HelpSection icon={FileText} title="Application Process" titleAr="عملية التطبيق">
              <div className="space-y-4">
                <p className="mb-6">
                  The trade license application follows a structured 5-state workflow that ensures 
                  all requirements are met before submission to UAE authorities.
                </p>
                <p dir="rtl" className="text-muted-foreground mb-6">
                  يتبع طلب الترخيص التجاري سير عمل منظم من 5 حالات يضمن استيفاء جميع المتطلبات 
                  قبل التقديم إلى السلطات الإماراتية.
                </p>

                <div className="space-y-4">
                  <ProcessStep
                    step={1}
                    title="Identity Verification"
                    titleAr="التحقق من الهوية"
                    description="Provide your Emirates ID for authentication and eligibility verification"
                    descriptionAr="قدم هويتك الإماراتية للمصادقة والتحقق من الأهلية"
                    icon={Users}
                    status="completed"
                  />
                  
                  <ProcessStep
                    step={2}
                    title="Company Details"
                    titleAr="تفاصيل الشركة"
                    description="Select legal form (LLC, Establishment, etc.), capital, and ownership structure"
                    descriptionAr="اختر الشكل القانوني (ذ.م.م، مؤسسة، إلخ)، رأس المال، وهيكل الملكية"
                    icon={Building2}
                    status="active"
                  />
                  
                  <ProcessStep
                    step={3}
                    title="Trade Name Reservation"
                    titleAr="حجز الاسم التجاري"
                    description="Choose and validate your business name availability using AI-powered checking"
                    descriptionAr="اختر واستخدم التحقق المدعوم بالذكاء الاصطناعي من توفر اسم عملك"
                    icon={Search}
                    status="pending"
                  />
                  
                  <ProcessStep
                    step={4}
                    title="Business Activities & Documents"
                    titleAr="أنشطة الأعمال والوثائق"
                    description="Select business activities, provide contact information, and upload required documents"
                    descriptionAr="اختر أنشطة الأعمال، قدم معلومات الاتصال، وارفع الوثائق المطلوبة"
                    icon={Upload}
                    status="pending"
                  />
                  
                  <ProcessStep
                    step={5}
                    title="Payment & License Issuance"
                    titleAr="الدفع وإصدار الترخيص"
                    description="Complete payment and receive your official trade license certificate"
                    descriptionAr="أكمل الدفع واستلم شهادة الترخيص التجاري الرسمية"
                    icon={CreditCard}
                    status="pending"
                  />
                </div>
              </div>
            </HelpSection>

            {/* FAQ Section */}
            <HelpSection icon={HelpCircle} title="Frequently Asked Questions" titleAr="الأسئلة الشائعة">
              <div className="space-y-4">
                <FAQItem
                  question="How long does the trade license application process take?"
                  questionAr="كم من الوقت تستغرق عملية طلب الترخيص التجاري؟"
                  answer="The typical processing time is 3-5 business days after all documents are submitted and payment is completed. Our AI system helps expedite the process by ensuring all requirements are met upfront."
                  answerAr="وقت المعالجة المعتاد هو 3-5 أيام عمل بعد تقديم جميع الوثائق وإتمام الدفع. نظامنا الذكي يساعد في تسريع العملية من خلال ضمان استيفاء جميع المتطلبات مقدماً."
                />
                
                <FAQItem
                  question="Can I modify my business activities after license issuance?"
                  questionAr="هل يمكنني تعديل أنشطة عملي بعد إصدار الترخيص؟"
                  answer="Yes, you can add or modify business activities through a license amendment process. Additional fees may apply depending on the new activities."
                  answerAr="نعم، يمكنك إضافة أو تعديل أنشطة الأعمال من خلال عملية تعديل الترخيص. قد تنطبق رسوم إضافية حسب الأنشطة الجديدة."
                />
                
                <FAQItem
                  question="What if my trade name is not available?"
                  questionAr="ماذا لو لم يكن اسمي التجاري متاحاً؟"
                  answer="Our AI system will automatically suggest alternative names based on your business type and preferences. You can also use our Arabic-English transliteration suggestions."
                  answerAr="نظامنا الذكي سيقترح تلقائياً أسماء بديلة بناءً على نوع عملك وتفضيلاتك. يمكنك أيضاً استخدام اقتراحات النقل الحرفي العربي-الإنجليزي."
                />
                
                <FAQItem
                  question="Do I need to visit a physical office?"
                  questionAr="هل أحتاج لزيارة مكتب فعلي؟"
                  answer="No, the entire process is digital. You can complete your application, upload documents, make payments, and receive your license certificate online."
                  answerAr="لا، العملية بأكملها رقمية. يمكنك إكمال طلبك ورفع الوثائق والدفع واستلام شهادة الترخيص عبر الإنترنت."
                />
                
                <FAQItem
                  question="What are the different types of business licenses available?"
                  questionAr="ما هي أنواع التراخيص التجارية المختلفة المتاحة؟"
                  answer="UAE offers Commercial, Professional, Industrial, and Tourism licenses. Each type has specific requirements and allowed activities. Our AI assistant will help you choose the right type based on your business needs."
                  answerAr="تقدم الإمارات تراخيص تجارية ومهنية وصناعية وسياحية. كل نوع له متطلبات وأنشطة مسموحة محددة. مساعدنا الذكي سيساعدك في اختيار النوع المناسب بناءً على احتياجات عملك."
                />
                
                <FAQItem
                  question="What documents are required for trade license application?"
                  questionAr="ما هي الوثائق المطلوبة لطلب الترخيص التجاري؟"
                  answer="Required documents include: Emirates ID, Passport copy, Entry permit, Passport-size photographs, NOC from sponsor (if applicable), Memorandum of Association (for companies), and business plan."
                  answerAr="الوثائق المطلوبة تشمل: الهوية الإماراتية، نسخة جواز السفر، تصريح الدخول، صور بحجم جواز السفر، عدم ممانعة من الكفيل (إن وجد)، عقد التأسيس (للشركات)، وخطة العمل."
                />
              </div>
            </HelpSection>

            {/* Contact Information */}
            <HelpSection icon={Phone} title="Contact & Support" titleAr="الاتصال والدعم">
              <div className="space-y-4">
                <p>
                  Need additional assistance? Our support team is available to help you with your trade license application.
                </p>
                <p dir="rtl" className="text-muted-foreground">
                  تحتاج مساعدة إضافية؟ فريق الدعم لدينا متاح لمساعدتك في طلب الترخيص التجاري.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <Phone className="h-5 w-5 text-blue-600" />
                      <div>
                        <p className="font-medium">Phone Support</p>
                        <p className="text-sm text-muted-foreground">+971 2 123 4567</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <Mail className="h-5 w-5 text-blue-600" />
                      <div>
                        <p className="font-medium">Email Support</p>
                        <p className="text-sm text-muted-foreground">support@tradelicense.ae</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <Clock className="h-5 w-5 text-blue-600" />
                      <div>
                        <p className="font-medium">Business Hours</p>
                        <p className="text-sm text-muted-foreground">Sun-Thu: 8:00 AM - 6:00 PM</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-4" dir="rtl">
                    <div className="flex items-center gap-3">
                      <Phone className="h-5 w-5 text-blue-600" />
                      <div>
                        <p className="font-medium">الدعم الهاتفي</p>
                        <p className="text-sm text-muted-foreground">+971 2 123 4567</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <Mail className="h-5 w-5 text-blue-600" />
                      <div>
                        <p className="font-medium">دعم البريد الإلكتروني</p>
                        <p className="text-sm text-muted-foreground">support@tradelicense.ae</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <Clock className="h-5 w-5 text-blue-600" />
                      <div>
                        <p className="font-medium">ساعات العمل</p>
                        <p className="text-sm text-muted-foreground">الأحد-الخميس: 8:00 ص - 6:00 م</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </HelpSection>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
              <div 
                className="p-6 text-center hover:bg-muted/20 transition-colors cursor-pointer rounded-lg"
                onClick={() => handleNavigation('/chat')}
              >
                <MessageCircle className="h-8 w-8 text-blue-600 mx-auto mb-3" />
                <h3 className="font-medium mb-2">Start New Application</h3>
                <p className="text-sm text-muted-foreground mb-1">Begin your trade license journey</p>
                <p className="text-sm text-muted-foreground" dir="rtl">ابدأ رحلة الترخيص التجاري</p>
              </div>
              
              <div 
                className="p-6 text-center hover:bg-muted/20 transition-colors cursor-pointer rounded-lg"
                onClick={() => handleNavigation('/chat')}
              >
                <Search className="h-8 w-8 text-green-600 mx-auto mb-3" />
                <h3 className="font-medium mb-2">Check Trade Name</h3>
                <p className="text-sm text-muted-foreground mb-1">Verify name availability</p>
                <p className="text-sm text-muted-foreground" dir="rtl">تحقق من توفر الاسم</p>
              </div>
              
              <div className="p-6 text-center hover:bg-muted/20 transition-colors cursor-pointer rounded-lg">
                <Download className="h-8 w-8 text-purple-600 mx-auto mb-3" />
                <h3 className="font-medium mb-2">Download Certificate</h3>
                <p className="text-sm text-muted-foreground mb-1">Get your license document</p>
                <p className="text-sm text-muted-foreground" dir="rtl">احصل على وثيقة الترخيص</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}