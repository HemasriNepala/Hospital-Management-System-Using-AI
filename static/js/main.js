// Hospital Management - simple UX helpers
document.addEventListener('DOMContentLoaded', function() {
  // --- Language switcher (simple client-side i18n) ---
  const I18N = {
    en: {
      'nav.language': 'Language',
      'nav.my_account': 'My Account',
      'nav.patient_dashboard': 'My Dashboard',
      'nav.patient_appointments': 'My Appointments',
      'nav.patient_prescriptions': 'My Prescriptions',
      'nav.patient_reports': 'My Reports',
      'nav.doctor_dashboard': 'My Dashboard',
      'nav.doctor_schedule': 'My Schedule',
      'nav.doctor_timings': 'Set My Timings',
      'nav.admin_dashboard': 'Dashboard',
      'nav.admin_doctors': 'Doctors',
      'nav.admin_patients': 'Patients',
      'nav.admin_appointments': 'Appointments',
      'nav.admin_beds': 'Beds',
      'nav.admin_callbacks': 'Call Requests',
      'nav.admin_reports': 'Reports',
      'nav.login': 'Log In',
      'nav.signup': 'Sign Up',
      'nav.logout': 'Log Out',
    },
    te: {
      'nav.language': 'భాష',
      'nav.my_account': 'నా ఖాతా',
      'nav.patient_dashboard': 'నా డ్యాష్‌బోర్డ్',
      'nav.patient_appointments': 'నా అపాయింట్‌మెంట్లు',
      'nav.patient_prescriptions': 'నా ప్రిస్క్రిప్షన్లు',
      'nav.patient_reports': 'నా రిపోర్టులు',
      'nav.doctor_dashboard': 'నా డ్యాష్‌బోర్డ్',
      'nav.doctor_schedule': 'నా షెడ్యూల్',
      'nav.doctor_timings': 'నా టైమింగ్స్',
      'nav.admin_dashboard': 'డ్యాష్‌బోర్డ్',
      'nav.admin_doctors': 'డాక్టర్లు',
      'nav.admin_patients': 'రోగులు',
      'nav.admin_appointments': 'అపాయింట్‌మెంట్లు',
      'nav.admin_beds': 'బెడ్లు',
      'nav.admin_callbacks': 'కాల్స్ అభ్యర్థనలు',
      'nav.admin_reports': 'రిపోర్టులు',
      'nav.login': 'లాగిన్',
      'nav.signup': 'సైన్ అప్',
      'nav.logout': 'లాగ్ అవుట్',
    },
    hi: {
      'nav.language': 'भाषा',
      'nav.my_account': 'मेरा खाता',
      'nav.patient_dashboard': 'मेरा डैशबोर्ड',
      'nav.patient_appointments': 'मेरी अपॉइंटमेंट',
      'nav.patient_prescriptions': 'मेरी पर्ची',
      'nav.patient_reports': 'मेरी रिपोर्ट',
      'nav.doctor_dashboard': 'मेरा डैशबोर्ड',
      'nav.doctor_schedule': 'मेरा शेड्यूल',
      'nav.doctor_timings': 'समय सेट करें',
      'nav.admin_dashboard': 'डैशबोर्ड',
      'nav.admin_doctors': 'डॉक्टर',
      'nav.admin_patients': 'मरीज',
      'nav.admin_appointments': 'अपॉइंटमेंट',
      'nav.admin_beds': 'बेड',
      'nav.admin_callbacks': 'कॉल अनुरोध',
      'nav.admin_reports': 'रिपोर्ट',
      'nav.login': 'लॉगिन',
      'nav.signup': 'साइन अप',
      'nav.logout': 'लॉग आउट',
    }
  };

  function getLang() {
    return localStorage.getItem('lang') || 'en';
  }

  function applyLang(lang) {
    const dict = I18N[lang] || I18N.en;
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (dict[key]) el.textContent = dict[key];
    });
    document.documentElement.setAttribute('lang', lang);
  }

  document.querySelectorAll('[data-set-lang]').forEach(btn => {
    btn.addEventListener('click', () => {
      const lang = btn.getAttribute('data-set-lang') || 'en';
      localStorage.setItem('lang', lang);
      applyLang(lang);
    });
  });
  applyLang(getLang());

  // Auto-dismiss alerts after 5 seconds
  var alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(function(alert) {
    setTimeout(function() {
      var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });
  // --- AI Wait Time Fetching ---
  function updateWaitTime() {
    fetch('/ai/waiting-time')
      .then(res => res.json())
      .then(data => {
        const el = document.getElementById('waitTime');
        if (el) el.textContent = data.prediction || 'Calculating...';
      }).catch(err => console.error('AI Wait Time failed:', err));
  }
  if (document.getElementById('aiWaitBadge')) {
    updateWaitTime();
    setInterval(updateWaitTime, 60000); // Update every minute
  }

  // --- Voice Assistant (Speech to Task) ---
  const voiceBtn = document.getElementById('voiceAssistantBtn');
  if (voiceBtn) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.lang = getLang() === 'te' ? 'te-IN' : (getLang() === 'hi' ? 'hi-IN' : 'en-US');

      voiceBtn.addEventListener('click', () => {
        recognition.start();
        voiceBtn.classList.add('btn-danger');
        voiceBtn.innerHTML = '<i class="bi bi-mic-fill"></i> Listening...';
      });

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript.toLowerCase();
        console.log('Voice Command:', transcript);
        voiceBtn.classList.remove('btn-danger');
        voiceBtn.innerHTML = '<i class="bi bi-mic"></i> Voice Help';
        
        // Simple logic for voice commands
        if (transcript.includes('dashboard') || transcript.includes('డ్యాష్‌బోర్డ్')) {
          location.href = '/dashboard';
        } else if (transcript.includes('appointment') || transcript.includes('అపాయింట్మెంట్')) {
          location.href = '/patient/book-appointment';
        } else {
          alert("You said: " + transcript + ". I'm learning more commands!");
        }
      };

      recognition.onerror = () => {
        voiceBtn.classList.remove('btn-danger');
        voiceBtn.innerHTML = '<i class="bi bi-mic"></i> Voice Help';
      };
    } else {
      voiceBtn.style.display = 'none';
    }
  }

  // --- Voice to Prescription (Doctor only) ---
  const micPresc = document.getElementById('micPrescription');
  if (micPresc) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    micPresc.addEventListener('click', () => {
      recognition.start();
      micPresc.classList.add('text-danger');
    });
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      const target = document.querySelector('textarea[name="medicines"]');
      if (target) {
        target.value += (target.value ? ', ' : '') + transcript;
      }
      micPresc.classList.remove('text-danger');
    };
  }
});
