document.querySelectorAll('input[name=aadhaar]').forEach(el=>el.addEventListener('blur',()=>{if(el.value&&!/^[2-9][0-9]{11}$/.test(el.value)){alert('Invalid Aadhaar')}}));
document.querySelectorAll('input[name=bank_ifsc]').forEach(el=>el.addEventListener('blur',()=>{if(el.value&&!/^[A-Z]{4}0[A-Z0-9]{6}$/i.test(el.value)){alert('Invalid IFSC')}}));
