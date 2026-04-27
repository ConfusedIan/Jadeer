(function(){
  const LANG_KEY = 'jadeer.lang';

  const DICT = {
    en:{
      brand:'Jadeer',
      welcome:'Welcome to Jadeer', welcome_sub:'Sign in to your account or create a new one',
      login:'Login', signup:'Sign Up',
      email:'Email', password:'Password', full_name:'Full Name', repeat_password:'Repeat Password',
      i_am_a:'I am a:', candidate:'Candidate', employer:'Employer',
      loading:'Loading…',
      pw_rule_len:'Must be at least 8 characters long',
      pw_rule_upper:'Must include at least 1 uppercase letter (A–Z)',
      pw_rule_lower:'Must include at least 1 lowercase letter (a–z)',
      pw_rule_num:'Must include at least 1 number (0–9)',
      pw_rule_special:'Must include at least 1 special character (e.g. ! @ # $ % ^ & *)',
      pw_rule_space:'Cannot contain spaces',
      // Dashboard / nav
      nav_profile:'Profile', nav_skills:'Skills', nav_certs:'Certificates',
      nav_recs:'Get Recommendations', nav_cvs:'My CVs', nav_chats:'Chats',
      nav_search:'Search',
      nav_contact:'Contact Us',
      contact_title:'Contact Us',
      contact_sub:'Have a question or feedback? We\'d love to hear from you.',
      contact_name:'Name', contact_name_placeholder:'Your name',
      contact_email:'Email',
      contact_message:'Message', contact_msg_placeholder:'Write your message here…',
      contact_send:'Send Message',
      contact_success_title:'Message sent!',
      contact_success_sub:'Thank you for reaching out. We\'ll get back to you soon.',
      welcome_back:'Welcome back!',
      manage_sub:'Manage your profile, skills, and career opportunities',
      view_profile:'View Profile', manage_skills:'Manage Skills', my_cvs:'My CVs',
      certificates:'Certificates', messages:'Messages',
      update_info:'Update your personal information',
      add_assess_skills:'Add and assess your skills',
      view_manage_cvs:'View and manage your CVs',
      manage_certs:'Manage your certifications',
      check_emp_msgs:'Check employer messages',
      ready_next:'Ready to find your next opportunity?',
      complete_and_generate:'Complete your profile and generate tailored CVs to match with potential employers.',
      get_recs:'Get Recommendations', complete_profile:'Complete Profile',
      logout:'Log out',
      // errors
      err_generic:'Something went wrong. Please try again.',
      err_passwords_match:'Passwords do not match.',
      err_pw_invalid:'Password does not meet the requirements.',
      err_fill_all:'Please fill in all required fields.',
    },
    ar:{
      brand:'جدير',
      welcome:'مرحباً بك في جدير', welcome_sub:'سجّل الدخول إلى حسابك أو أنشئ حساباً جديداً',
      login:'تسجيل الدخول', signup:'إنشاء حساب',
      email:'البريد الإلكتروني', password:'كلمة المرور', full_name:'الاسم الكامل', repeat_password:'تأكيد كلمة المرور',
      i_am_a:'أنا:', candidate:'مرشح', employer:'صاحب عمل',
      loading:'جار التحميل…',
      pw_rule_len:'يجب أن لا تقل عن 8 أحرف',
      pw_rule_upper:'يجب أن تحتوي على حرف كبير واحد على الأقل (A–Z)',
      pw_rule_lower:'يجب أن تحتوي على حرف صغير واحد على الأقل (a–z)',
      pw_rule_num:'يجب أن تحتوي على رقم واحد على الأقل (0–9)',
      pw_rule_special:'يجب أن تحتوي على رمز خاص واحد على الأقل (! @ # $ % ^ & *)',
      pw_rule_space:'لا يمكن أن تحتوي على مسافات',
      nav_profile:'الملف الشخصي', nav_skills:'المهارات', nav_certs:'الشهادات',
      nav_recs:'التوصيات', nav_cvs:'سيري الذاتية', nav_chats:'المحادثات',
      nav_search:'البحث',
      nav_contact:'تواصل معنا',
      contact_title:'تواصل معنا',
      contact_sub:'هل لديك سؤال أو ملاحظة؟ يسعدنا سماعك.',
      contact_name:'الاسم', contact_name_placeholder:'اسمك الكامل',
      contact_email:'البريد الإلكتروني',
      contact_message:'الرسالة', contact_msg_placeholder:'اكتب رسالتك هنا…',
      contact_send:'إرسال الرسالة',
      contact_success_title:'تم الإرسال!',
      contact_success_sub:'شكراً للتواصل معنا. سنرد عليك في أقرب وقت.',
      welcome_back:'مرحباً بعودتك!',
      manage_sub:'أدر ملفك الشخصي ومهاراتك وفرصك المهنية',
      view_profile:'عرض الملف', manage_skills:'إدارة المهارات', my_cvs:'سيري الذاتية',
      certificates:'الشهادات', messages:'الرسائل',
      update_info:'حدّث معلوماتك الشخصية',
      add_assess_skills:'أضف مهاراتك وقم بتقييمها',
      view_manage_cvs:'اعرض وأدر سيرك الذاتية',
      manage_certs:'أدر شهاداتك',
      check_emp_msgs:'تحقق من رسائل أصحاب العمل',
      ready_next:'جاهز لإيجاد فرصتك القادمة؟',
      complete_and_generate:'أكمل ملفك الشخصي وأنشئ سيراً ذاتية مخصصة لتتوافق مع أصحاب العمل المحتملين.',
      get_recs:'احصل على التوصيات', complete_profile:'أكمل الملف',
      logout:'تسجيل الخروج',
      err_generic:'حدث خطأ ما. يُرجى المحاولة مرة أخرى.',
      err_passwords_match:'كلمتا المرور غير متطابقتين.',
      err_pw_invalid:'كلمة المرور لا تستوفي الشروط.',
      err_fill_all:'يُرجى تعبئة جميع الحقول المطلوبة.',
    }
  };

  let lang = localStorage.getItem(LANG_KEY) || 'en';

  function t(key){ return (DICT[lang] && DICT[lang][key]) || DICT.en[key] || key; }
  function getLang(){ return lang; }
  function setLang(l){
    lang = l;
    localStorage.setItem(LANG_KEY,l);
    document.documentElement.lang = l;
    document.documentElement.dir = l==='ar'?'rtl':'ltr';
    applyTranslations();
    window.dispatchEvent(new Event('langchange'));
  }
  function applyTranslations(root=document){
    // Always read via the public t() so monkey-patches from phase2/phase2b
    // extension files are honored. (Earlier bug: closure-local t() was baked in
    // at module load and never saw the extra dictionaries.)
    const tr = (window.JadeerI18n && window.JadeerI18n.t) || t;
    root.querySelectorAll('[data-i18n]').forEach(el=>{
      el.textContent = tr(el.getAttribute('data-i18n'));
    });
    root.querySelectorAll('[data-i18n-ph]').forEach(el=>{
      el.placeholder = tr(el.getAttribute('data-i18n-ph'));
    });
  }
  function toggleLang(){ setLang(lang==='en'?'ar':'en'); }

  // Initial apply
  document.addEventListener('DOMContentLoaded',()=>{
    document.documentElement.lang = lang;
    document.documentElement.dir = lang==='ar'?'rtl':'ltr';
  });

  window.JadeerI18n = { t, getLang, setLang, toggleLang, applyTranslations };
})();
