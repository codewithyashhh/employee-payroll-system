function toggleSalaryFields(){
  const type=(document.getElementById('employee_type')||{}).value;
  document.querySelectorAll('.type-block').forEach(el=>el.style.display='none');
  if(type==='SM') document.querySelectorAll('.salary-sm').forEach(el=>el.style.display='block');
  if(type==='Labour') document.querySelectorAll('.salary-labour').forEach(el=>el.style.display='block');
  if(type==='ANL') document.querySelectorAll('.salary-anl').forEach(el=>el.style.display='grid');
}
const employeeType=document.getElementById('employee_type');
if(employeeType){employeeType.addEventListener('change',toggleSalaryFields);toggleSalaryFields();}
document.querySelectorAll('input[name=aadhaar]').forEach(el=>el.addEventListener('blur',()=>{if(el.value&&!/^[2-9][0-9]{11}$/.test(el.value)){alert('Invalid Aadhaar')}}));
document.querySelectorAll('input[name=bank_ifsc]').forEach(el=>el.addEventListener('blur',()=>{if(el.value&&!/^[A-Z]{4}0[A-Z0-9]{6}$/i.test(el.value)){alert('Invalid IFSC')}}));
