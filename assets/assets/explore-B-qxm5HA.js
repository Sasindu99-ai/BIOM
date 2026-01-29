let o=1,i=1,c=!1,r=!1,m="";async function u(t,e,s){const a=new URLSearchParams({page:e,limit:12});return s&&a.append("search",s),(await fetch(`${t==="studies"?"/api/v1/study/":"/api/v1/study/biomarkers/"}?${a.toString()}`)).json()}function y(t){return`
    <div class="col-md-6 col-xl-4">
      <div class="card h-100">
        <div class="card-body">
          <h5 class="card-title">${t.name??"Study"}</h5>
          <p class="card-text text-muted">${t.description??""}</p>
        </div>
      </div>
    </div>`}function g(t){return`
    <div class="col-md-6 col-xl-4">
      <div class="card h-100">
        <div class="card-body">
          <h5 class="card-title">${t.name??"Biomarker"}</h5>
          <p class="card-text text-muted">${t.category??""}</p>
        </div>
      </div>
    </div>`}async function l(t=!0){if(c)return;const e=document.getElementById("studiesLoading"),s=document.getElementById("studiesEnd"),a=document.getElementById("studiesContainer");e==null||e.classList.remove("d-none");const n=await u("studies",o,m),d=n.results??n.items??[];t||(a.innerHTML=""),a.insertAdjacentHTML("beforeend",d.map(y).join("")),!(n.pagination&&n.pagination.has_next||n.page<n.total_pages)||d.length===0?(c=!0,s==null||s.classList.remove("d-none")):o+=1,e==null||e.classList.add("d-none")}async function f(t=!0){if(r)return;const e=document.getElementById("biomarkersLoading"),s=document.getElementById("biomarkersEnd"),a=document.getElementById("biomarkersContainer");e==null||e.classList.remove("d-none");const n=await u("biomarkers",i,m),d=n.results??n.items??[];t||(a.innerHTML=""),a.insertAdjacentHTML("beforeend",d.map(g).join("")),!(n.pagination&&n.pagination.has_next||n.page<n.total_pages)||d.length===0?(r=!0,s==null||s.classList.remove("d-none")):i+=1,e==null||e.classList.add("d-none")}function p(){var s;const e=((s=document.querySelector("#exploreTabs .nav-link.active"))==null?void 0:s.id)==="studies-tab"?"studies":"biomarkers";window.innerHeight+window.scrollY>=document.body.offsetHeight-300&&(e==="studies"?l(!0):f(!0))}document.addEventListener("DOMContentLoaded",()=>{if(!document.getElementById("exploreTabs"))return;l(!0);const t=document.getElementById("searchBtn"),e=document.getElementById("searchInput");t==null||t.addEventListener("click",()=>{var s,a;m=(e==null?void 0:e.value)||"",o=1,i=1,c=!1,r=!1,(s=document.getElementById("studiesEnd"))==null||s.classList.add("d-none"),(a=document.getElementById("biomarkersEnd"))==null||a.classList.add("d-none"),l(!1),f(!1)}),window.addEventListener("scroll",p)});
