import{c as x,a as t,b as s,d as e,f as C,g as S,F as g,r as y,e as f,u as p,k as D,t as r,i as v,j as n,n as M}from"./index-BWVJaaS9.js";/**
 * @license lucide-vue-next v0.368.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const V=x("FileTextIcon",[["path",{d:"M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z",key:"1rqfz7"}],["path",{d:"M14 2v4a2 2 0 0 0 2 2h4",key:"tnqrlb"}],["path",{d:"M10 9H8",key:"b1mrlr"}],["path",{d:"M16 13H8",key:"t4e002"}],["path",{d:"M16 17H8",key:"z1uh3a"}]]);/**
 * @license lucide-vue-next v0.368.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const H=x("GitCommitHorizontalIcon",[["circle",{cx:"12",cy:"12",r:"3",key:"1v7zrd"}],["line",{x1:"3",x2:"9",y1:"12",y2:"12",key:"1dyftd"}],["line",{x1:"15",x2:"21",y1:"12",y2:"12",key:"oup4p8"}]]),T={class:"h-full flex flex-col space-y-6"},N={class:"bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex-shrink-0"},F={class:"grid grid-cols-1 md:grid-cols-2 gap-4 items-end"},I=["value"],R={key:0,class:"grid grid-cols-1 md:grid-cols-3 gap-6 flex-1 min-h-0"},E={class:"bg-white rounded-xl shadow-sm border border-gray-200 p-4 overflow-y-auto"},L={class:"text-md font-bold text-gray-800 mb-3 flex items-center"},O={key:0,class:"text-center py-4 text-gray-500"},z={key:1,class:"space-y-3"},B=["onClick"],G={class:"font-medium text-sm text-gray-800"},j={class:"text-xs text-gray-500 mt-1 mt-1 flex justify-between"},A={class:"font-mono text-[10px] text-gray-400"},q={key:2,class:"text-center py-8 text-gray-400 text-sm"},J={class:"bg-gray-900 rounded-xl shadow-sm border border-gray-700 p-0 md:col-span-2 overflow-hidden flex flex-col"},U={class:"bg-gray-800 px-4 py-3 border-b border-gray-700 flex justify-between items-center text-gray-300"},W={class:"text-sm font-medium flex items-center"},Z={key:0},$={key:1},K={class:"p-4 overflow-auto flex-1 h-full"},P={key:0,class:"text-center py-12 text-gray-500"},Q={key:1,class:"text-xs text-green-400 font-mono whitespace-pre-wrap leading-relaxed"},X={key:2,class:"h-full flex items-center justify-center text-gray-600 text-sm"},Y={key:0},ae={__name:"ConfigDiff",setup(ee){const _=n([{id:1,hostname:"CORE-RT-01",vendor:"Cisco IOS",ip_address:"10.0.0.1"},{id:2,hostname:"ACC-SW-04",vendor:"Juniper Junos",ip_address:"10.0.4.15"}]),d=n(""),i=n(""),u=n([]),l=n(""),m=n(!1),h=n(!1),b=c=>{const a={year:"numeric",month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"};return new Date(c).toLocaleDateString(void 0,a)},k=()=>{d.value&&(m.value=!0,i.value="",l.value="",setTimeout(()=>{m.value=!1,u.value=[{commit_hash:"a1b2c3d4e5f6",date:new Date().toISOString(),message:"Automated config backup for CORE-RT-01",author:"NMS Bot"},{commit_hash:"f6e5d4c3b2a1",date:new Date(Date.now()-864e5).toISOString(),message:"Added new VLAN 100 via Dashboard",author:"Hendra"},{commit_hash:"9081726354ab",date:new Date(Date.now()-1728e5).toISOString(),message:"Initial configuration snapshot",author:"NMS Bot"}]},800))},w=c=>{i.value=c,h.value=!0,setTimeout(()=>{h.value=!1,l.value=`!
! Last configuration change by NMS Framework
!
hostname CORE-RT-01
!
interface GigabitEthernet0/0
 ip address 10.0.0.1 255.255.255.0
 no shutdown
!
interface Vlan100
 description SERVER_MGMT
 ip address 192.168.100.1 255.255.255.0
!
router bgp 65000
 neighbor 10.0.0.2 remote-as 65001
!
end`},500)};return(c,a)=>(t(),s("div",T,[e("div",N,[a[3]||(a[3]=e("h2",{class:"text-lg font-semibold text-gray-800 mb-4"},"Configuration Diff Viewer",-1)),e("div",F,[e("div",null,[a[2]||(a[2]=e("label",{class:"block text-sm font-medium text-gray-700 mb-1"},"Target Device",-1)),C(e("select",{"onUpdate:modelValue":a[0]||(a[0]=o=>d.value=o),onChange:k,class:"w-full border-gray-300 rounded-lg shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm p-2 bg-gray-50 border"},[a[1]||(a[1]=e("option",{value:"",disabled:""},"Select a device",-1)),(t(!0),s(g,null,y(_.value,o=>(t(),s("option",{key:o.id,value:o.id},r(o.hostname)+" - "+r(o.ip_address),9,I))),128))],544),[[S,d.value]])])])]),d.value?(t(),s("div",R,[e("div",E,[e("h3",L,[f(p(H),{class:"w-5 h-5 mr-2 text-primary-500"}),a[4]||(a[4]=D(" Backup History (Git) ",-1))]),m.value?(t(),s("div",O,"Loading history...")):u.value.length>0?(t(),s("div",z,[(t(!0),s(g,null,y(u.value,(o,te)=>(t(),s("div",{key:o.commit_hash,onClick:se=>w(o.commit_hash),class:M(["p-3 border rounded-lg cursor-pointer transition",i.value===o.commit_hash?"bg-primary-50 border-primary-500 ring-1 ring-primary-500":"bg-gray-50 border-gray-100 hover:bg-gray-100"])},[e("div",G,r(o.message),1),e("div",j,[e("span",null,r(b(o.date)),1),e("span",A,r(o.commit_hash.substring(0,7)),1)])],10,B))),128))])):(t(),s("div",q," No backup history found for this device. "))]),e("div",J,[e("div",U,[e("span",W,[f(p(V),{class:"w-4 h-4 mr-2"}),i.value?(t(),s("span",Z,"Viewing File @ "+r(i.value.substring(0,7)),1)):(t(),s("span",$,"Select a commit to view configuration"))])]),e("div",K,[h.value?(t(),s("div",P,"Loading file content...")):l.value?(t(),s("pre",Q,r(l.value),1)):(t(),s("div",X,[d.value&&!i.value?(t(),s("span",Y,"Click a commit on the left to see the configuration file content.")):v("",!0)]))])])])):v("",!0)]))}};export{ae as default};
