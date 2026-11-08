import{r as f,f as On,N as on,j as i,c as we,u as Tn,a as it}from"./index-CbKSqT-t.js";import{u as Q,d as U,V as j,D as Te,e as X,P as Qe,f as Je,v as an,M as Ie,T as Be,S as zt,Q as Gt,R as Ln,g as Rn,I as Cn,F as Ut,h as _t,i as ze,W as Dn,j as Tt,k as cn,l as ln,U as kt,m as Wt,n as Nn,o as ke,L as In,p as Bn,q as zn,a as je,r as Gn,s as Un,t as kn,A as Wn,w as un,x as Hn,C as Fn,y as Vn,c as dn,z as $n}from"./Gltf-OG4v4jOm.js";function Le(){return Le=Object.assign?Object.assign.bind():function(n){for(var t=1;t<arguments.length;t++){var s=arguments[t];for(var e in s)({}).hasOwnProperty.call(s,e)&&(n[e]=s[e])}return n},Le.apply(null,arguments)}const tt=new j,Lt=new j,Yn=new j,Ht=new X;function Xn(n,t,s){const e=tt.setFromMatrixPosition(n.matrixWorld);e.project(t);const r=s.width/2,o=s.height/2;return[e.x*r+r,-(e.y*o)+o]}function Zn(n,t){const s=tt.setFromMatrixPosition(n.matrixWorld),e=Lt.setFromMatrixPosition(t.matrixWorld),r=s.sub(e),o=t.getWorldDirection(Yn);return r.angleTo(o)>Math.PI/2}function Kn(n,t,s,e){const r=tt.setFromMatrixPosition(n.matrixWorld),o=r.clone();o.project(t),Ht.set(o.x,o.y),s.setFromCamera(Ht,t);const u=s.intersectObjects(e,!0);if(u.length){const c=u[0].distance;return r.distanceTo(s.ray.origin)<c}return!0}function qn(n,t){if(t instanceof Je)return t.zoom;if(t instanceof Qe){const s=tt.setFromMatrixPosition(n.matrixWorld),e=Lt.setFromMatrixPosition(t.matrixWorld),r=t.fov*Math.PI/180,o=s.distanceTo(e);return 1/(2*Math.tan(r/2)*o)}else return 1}function Qn(n,t,s){if(t instanceof Qe||t instanceof Je){const e=tt.setFromMatrixPosition(n.matrixWorld),r=Lt.setFromMatrixPosition(t.matrixWorld),o=e.distanceTo(r),u=(s[1]-s[0])/(t.far-t.near),c=s[1]-u*t.far;return Math.round(u*o+c)}}const Ot=n=>Math.abs(n)<1e-10?0:n;function fn(n,t,s=""){let e="matrix3d(";for(let r=0;r!==16;r++)e+=Ot(t[r]*n.elements[r])+(r!==15?",":")");return s+e}const Jn=(n=>t=>fn(t,n))([1,-1,1,1,1,-1,1,1,1,-1,1,1,1,-1,1,1]),es=(n=>(t,s)=>fn(t,n(s),"translate(-50%,-50%)"))(n=>[1/n,1/n,1/n,1,-1/n,-1/n,-1/n,-1,1/n,1/n,1/n,1,1,1,1,1]);function ts(n){return n&&typeof n=="object"&&"current"in n}const Re=f.forwardRef(({children:n,eps:t=.001,style:s,className:e,prepend:r,center:o,fullscreen:u,portal:c,distanceFactor:l,sprite:p=!1,transform:h=!1,occlude:d,onOcclude:m,castShadow:y,receiveShadow:P,material:T,geometry:L,zIndexRange:S=[16777271,0],calculatePosition:w=Xn,as:v="div",wrapperClass:M,pointerEvents:O="auto",...E},te)=>{const{gl:B,camera:C,scene:_,size:A,raycaster:J,events:Y,viewport:de}=Q(),[I]=f.useState(()=>document.createElement(v)),ye=f.useRef(),z=f.useRef(null),Z=f.useRef(0),ee=f.useRef([0,0]),ne=f.useRef(null),Ee=f.useRef(null),fe=(c==null?void 0:c.current)||Y.connected||B.domElement.parentNode,K=f.useRef(null),Se=f.useRef(!1),Ce=f.useMemo(()=>d&&d!=="blending"||Array.isArray(d)&&d.length&&ts(d[0]),[d]);f.useLayoutEffect(()=>{const $=B.domElement;d&&d==="blending"?($.style.zIndex=`${Math.floor(S[0]/2)}`,$.style.position="absolute",$.style.pointerEvents="none"):($.style.zIndex=null,$.style.position=null,$.style.pointerEvents=null)},[d]),f.useLayoutEffect(()=>{if(z.current){const $=ye.current=On.createRoot(I);if(_.updateMatrixWorld(),h)I.style.cssText="position:absolute;top:0;left:0;pointer-events:none;overflow:hidden;";else{const D=w(z.current,C,A);I.style.cssText=`position:absolute;top:0;left:0;transform:translate3d(${D[0]}px,${D[1]}px,0);transform-origin:0 0;`}return fe&&(r?fe.prepend(I):fe.appendChild(I)),()=>{fe&&fe.removeChild(I),$.unmount()}}},[fe,h]),f.useLayoutEffect(()=>{M&&(I.className=M)},[M]);const He=f.useMemo(()=>h?{position:"absolute",top:0,left:0,width:A.width,height:A.height,transformStyle:"preserve-3d",pointerEvents:"none"}:{position:"absolute",transform:o?"translate3d(-50%,-50%,0)":"none",...u&&{top:-A.height/2,left:-A.width/2,width:A.width,height:A.height},...s},[s,o,u,A,h]),gt=f.useMemo(()=>({position:"absolute",pointerEvents:O}),[O]);f.useLayoutEffect(()=>{if(Se.current=!1,h){var $;($=ye.current)==null||$.render(f.createElement("div",{ref:ne,style:He},f.createElement("div",{ref:Ee,style:gt},f.createElement("div",{ref:te,className:e,style:s,children:n}))))}else{var D;(D=ye.current)==null||D.render(f.createElement("div",{ref:te,style:He,className:e,children:n}))}});const ve=f.useRef(!0);U($=>{if(z.current){C.updateMatrixWorld(),z.current.updateWorldMatrix(!0,!1);const D=h?ee.current:w(z.current,C,A);if(h||Math.abs(Z.current-C.zoom)>t||Math.abs(ee.current[0]-D[0])>t||Math.abs(ee.current[1]-D[1])>t){const se=Zn(z.current,C);let q=!1;Ce&&(Array.isArray(d)?q=d.map(re=>re.current):d!=="blending"&&(q=[_]));const xe=ve.current;if(q){const re=Kn(z.current,C,J,q);ve.current=re&&!se}else ve.current=!se;xe!==ve.current&&(m?m(!ve.current):I.style.display=ve.current?"block":"none");const De=Math.floor(S[0]/2),yt=d?Ce?[S[0],De]:[De-1,0]:S;if(I.style.zIndex=`${Qn(z.current,C,yt)}`,h){const[re,Fe]=[A.width/2,A.height/2],Ne=C.projectionMatrix.elements[5]*Fe,{isOrthographicCamera:st,top:vt,left:rt,bottom:Ve,right:Pe}=C,xt=Jn(C.matrixWorldInverse),bt=st?`scale(${Ne})translate(${Ot(-(Pe+rt)/2)}px,${Ot((vt+Ve)/2)}px)`:`translateZ(${Ne}px)`;let oe=z.current.matrixWorld;p&&(oe=C.matrixWorldInverse.clone().transpose().copyPosition(oe).scale(z.current.scale),oe.elements[3]=oe.elements[7]=oe.elements[11]=0,oe.elements[15]=1),I.style.width=A.width+"px",I.style.height=A.height+"px",I.style.perspective=st?"":`${Ne}px`,ne.current&&Ee.current&&(ne.current.style.transform=`${bt}${xt}translate(${re}px,${Fe}px)`,Ee.current.style.transform=es(oe,1/((l||10)/400)))}else{const re=l===void 0?1:qn(z.current,C)*l;I.style.transform=`translate3d(${D[0]}px,${D[1]}px,0) scale(${re})`}ee.current=D,Z.current=C.zoom}}if(!Ce&&K.current&&!Se.current)if(h){if(ne.current){const D=ne.current.children[0];if(D!=null&&D.clientWidth&&D!=null&&D.clientHeight){const{isOrthographicCamera:se}=C;if(se||L)E.scale&&(Array.isArray(E.scale)?E.scale instanceof j?K.current.scale.copy(E.scale.clone().divideScalar(1)):K.current.scale.set(1/E.scale[0],1/E.scale[1],1/E.scale[2]):K.current.scale.setScalar(1/E.scale));else{const q=(l||10)/400,xe=D.clientWidth*q,De=D.clientHeight*q;K.current.scale.set(xe,De,1)}Se.current=!0}}}else{const D=I.children[0];if(D!=null&&D.clientWidth&&D!=null&&D.clientHeight){const se=1/de.factor,q=D.clientWidth*se,xe=D.clientHeight*se;K.current.scale.set(q,xe,1),Se.current=!0}K.current.lookAt($.camera.position)}});const nt=f.useMemo(()=>({vertexShader:h?void 0:`
          /*
            This shader is from the THREE's SpriteMaterial.
            We need to turn the backing plane into a Sprite
            (make it always face the camera) if "transfrom"
            is false.
          */
          #include <common>

          void main() {
            vec2 center = vec2(0., 1.);
            float rotation = 0.0;

            // This is somewhat arbitrary, but it seems to work well
            // Need to figure out how to derive this dynamically if it even matters
            float size = 0.03;

            vec4 mvPosition = modelViewMatrix * vec4( 0.0, 0.0, 0.0, 1.0 );
            vec2 scale;
            scale.x = length( vec3( modelMatrix[ 0 ].x, modelMatrix[ 0 ].y, modelMatrix[ 0 ].z ) );
            scale.y = length( vec3( modelMatrix[ 1 ].x, modelMatrix[ 1 ].y, modelMatrix[ 1 ].z ) );

            bool isPerspective = isPerspectiveMatrix( projectionMatrix );
            if ( isPerspective ) scale *= - mvPosition.z;

            vec2 alignedPosition = ( position.xy - ( center - vec2( 0.5 ) ) ) * scale * size;
            vec2 rotatedPosition;
            rotatedPosition.x = cos( rotation ) * alignedPosition.x - sin( rotation ) * alignedPosition.y;
            rotatedPosition.y = sin( rotation ) * alignedPosition.x + cos( rotation ) * alignedPosition.y;
            mvPosition.xy += rotatedPosition;

            gl_Position = projectionMatrix * mvPosition;
          }
      `,fragmentShader:`
        void main() {
          gl_FragColor = vec4(0.0, 0.0, 0.0, 0.0);
        }
      `}),[h]);return f.createElement("group",Le({},E,{ref:z}),d&&!Ce&&f.createElement("mesh",{castShadow:y,receiveShadow:P,ref:K},L||f.createElement("planeGeometry",null),T||f.createElement("shaderMaterial",{side:Te,vertexShader:nt.vertexShader,fragmentShader:nt.fragmentShader})))}),hn=an>=125?"uv1":"uv2";var ns=Object.defineProperty,ss=(n,t,s)=>t in n?ns(n,t,{enumerable:!0,configurable:!0,writable:!0,value:s}):n[t]=s,rs=(n,t,s)=>(ss(n,t+"",s),s);class os{constructor(){rs(this,"_listeners")}addEventListener(t,s){this._listeners===void 0&&(this._listeners={});const e=this._listeners;e[t]===void 0&&(e[t]=[]),e[t].indexOf(s)===-1&&e[t].push(s)}hasEventListener(t,s){if(this._listeners===void 0)return!1;const e=this._listeners;return e[t]!==void 0&&e[t].indexOf(s)!==-1}removeEventListener(t,s){if(this._listeners===void 0)return;const r=this._listeners[t];if(r!==void 0){const o=r.indexOf(s);o!==-1&&r.splice(o,1)}}dispatchEvent(t){if(this._listeners===void 0)return;const e=this._listeners[t.type];if(e!==void 0){t.target=this;const r=e.slice(0);for(let o=0,u=r.length;o<u;o++)r[o].call(this,t);t.target=null}}}var is=Object.defineProperty,as=(n,t,s)=>t in n?is(n,t,{enumerable:!0,configurable:!0,writable:!0,value:s}):n[t]=s,x=(n,t,s)=>(as(n,typeof t!="symbol"?t+"":t,s),s);const at=new Ln,Ft=new Rn,cs=Math.cos(70*(Math.PI/180)),Vt=(n,t)=>(n%t+t)%t;let ls=class extends os{constructor(t,s){super(),x(this,"object"),x(this,"domElement"),x(this,"enabled",!0),x(this,"target",new j),x(this,"minDistance",0),x(this,"maxDistance",1/0),x(this,"minZoom",0),x(this,"maxZoom",1/0),x(this,"minPolarAngle",0),x(this,"maxPolarAngle",Math.PI),x(this,"minAzimuthAngle",-1/0),x(this,"maxAzimuthAngle",1/0),x(this,"enableDamping",!1),x(this,"dampingFactor",.05),x(this,"enableZoom",!0),x(this,"zoomSpeed",1),x(this,"enableRotate",!0),x(this,"rotateSpeed",1),x(this,"enablePan",!0),x(this,"panSpeed",1),x(this,"screenSpacePanning",!0),x(this,"keyPanSpeed",7),x(this,"zoomToCursor",!1),x(this,"autoRotate",!1),x(this,"autoRotateSpeed",2),x(this,"reverseOrbit",!1),x(this,"reverseHorizontalOrbit",!1),x(this,"reverseVerticalOrbit",!1),x(this,"keys",{LEFT:"ArrowLeft",UP:"ArrowUp",RIGHT:"ArrowRight",BOTTOM:"ArrowDown"}),x(this,"mouseButtons",{LEFT:Ie.ROTATE,MIDDLE:Ie.DOLLY,RIGHT:Ie.PAN}),x(this,"touches",{ONE:Be.ROTATE,TWO:Be.DOLLY_PAN}),x(this,"target0"),x(this,"position0"),x(this,"zoom0"),x(this,"_domElementKeyEvents",null),x(this,"getPolarAngle"),x(this,"getAzimuthalAngle"),x(this,"setPolarAngle"),x(this,"setAzimuthalAngle"),x(this,"getDistance"),x(this,"getZoomScale"),x(this,"listenToKeyEvents"),x(this,"stopListenToKeyEvents"),x(this,"saveState"),x(this,"reset"),x(this,"update"),x(this,"connect"),x(this,"dispose"),x(this,"dollyIn"),x(this,"dollyOut"),x(this,"getScale"),x(this,"setScale"),this.object=t,this.domElement=s,this.target0=this.target.clone(),this.position0=this.object.position.clone(),this.zoom0=this.object.zoom,this.getPolarAngle=()=>h.phi,this.getAzimuthalAngle=()=>h.theta,this.setPolarAngle=a=>{let g=Vt(a,2*Math.PI),b=h.phi;b<0&&(b+=2*Math.PI),g<0&&(g+=2*Math.PI);let R=Math.abs(g-b);2*Math.PI-R<R&&(g<b?g+=2*Math.PI:b+=2*Math.PI),d.phi=g-b,e.update()},this.setAzimuthalAngle=a=>{let g=Vt(a,2*Math.PI),b=h.theta;b<0&&(b+=2*Math.PI),g<0&&(g+=2*Math.PI);let R=Math.abs(g-b);2*Math.PI-R<R&&(g<b?g+=2*Math.PI:b+=2*Math.PI),d.theta=g-b,e.update()},this.getDistance=()=>e.object.position.distanceTo(e.target),this.listenToKeyEvents=a=>{a.addEventListener("keydown",wt),this._domElementKeyEvents=a},this.stopListenToKeyEvents=()=>{this._domElementKeyEvents.removeEventListener("keydown",wt),this._domElementKeyEvents=null},this.saveState=()=>{e.target0.copy(e.target),e.position0.copy(e.object.position),e.zoom0=e.object.zoom},this.reset=()=>{e.target.copy(e.target0),e.object.position.copy(e.position0),e.object.zoom=e.zoom0,e.object.updateProjectionMatrix(),e.dispatchEvent(r),e.update(),l=c.NONE},this.update=(()=>{const a=new j,g=new j(0,1,0),b=new Gt().setFromUnitVectors(t.up,g),R=b.clone().invert(),G=new j,he=new Gt,be=2*Math.PI;return function(){const Bt=e.object.position;b.setFromUnitVectors(t.up,g),R.copy(b).invert(),a.copy(Bt).sub(e.target),a.applyQuaternion(b),h.setFromVector3(a),e.autoRotate&&l===c.NONE&&de(J()),e.enableDamping?(h.theta+=d.theta*e.dampingFactor,h.phi+=d.phi*e.dampingFactor):(h.theta+=d.theta,h.phi+=d.phi);let pe=e.minAzimuthAngle,me=e.maxAzimuthAngle;isFinite(pe)&&isFinite(me)&&(pe<-Math.PI?pe+=be:pe>Math.PI&&(pe-=be),me<-Math.PI?me+=be:me>Math.PI&&(me-=be),pe<=me?h.theta=Math.max(pe,Math.min(me,h.theta)):h.theta=h.theta>(pe+me)/2?Math.max(pe,h.theta):Math.min(me,h.theta)),h.phi=Math.max(e.minPolarAngle,Math.min(e.maxPolarAngle,h.phi)),h.makeSafe(),e.enableDamping===!0?e.target.addScaledVector(y,e.dampingFactor):e.target.add(y),e.zoomToCursor&&C||e.object.isOrthographicCamera?h.radius=K(h.radius):h.radius=K(h.radius*m),a.setFromSpherical(h),a.applyQuaternion(R),Bt.copy(e.target).add(a),e.object.matrixAutoUpdate||e.object.updateMatrix(),e.object.lookAt(e.target),e.enableDamping===!0?(d.theta*=1-e.dampingFactor,d.phi*=1-e.dampingFactor,y.multiplyScalar(1-e.dampingFactor)):(d.set(0,0,0),y.set(0,0,0));let $e=!1;if(e.zoomToCursor&&C){let Ye=null;if(e.object instanceof Qe&&e.object.isPerspectiveCamera){const Xe=a.length();Ye=K(Xe*m);const ot=Xe-Ye;e.object.position.addScaledVector(te,ot),e.object.updateMatrixWorld()}else if(e.object.isOrthographicCamera){const Xe=new j(B.x,B.y,0);Xe.unproject(e.object),e.object.zoom=Math.max(e.minZoom,Math.min(e.maxZoom,e.object.zoom/m)),e.object.updateProjectionMatrix(),$e=!0;const ot=new j(B.x,B.y,0);ot.unproject(e.object),e.object.position.sub(ot).add(Xe),e.object.updateMatrixWorld(),Ye=a.length()}else console.warn("WARNING: OrbitControls.js encountered an unknown camera type - zoom to cursor disabled."),e.zoomToCursor=!1;Ye!==null&&(e.screenSpacePanning?e.target.set(0,0,-1).transformDirection(e.object.matrix).multiplyScalar(Ye).add(e.object.position):(at.origin.copy(e.object.position),at.direction.set(0,0,-1).transformDirection(e.object.matrix),Math.abs(e.object.up.dot(at.direction))<cs?t.lookAt(e.target):(Ft.setFromNormalAndCoplanarPoint(e.object.up,e.target),at.intersectPlane(Ft,e.target))))}else e.object instanceof Je&&e.object.isOrthographicCamera&&($e=m!==1,$e&&(e.object.zoom=Math.max(e.minZoom,Math.min(e.maxZoom,e.object.zoom/m)),e.object.updateProjectionMatrix()));return m=1,C=!1,$e||G.distanceToSquared(e.object.position)>p||8*(1-he.dot(e.object.quaternion))>p?(e.dispatchEvent(r),G.copy(e.object.position),he.copy(e.object.quaternion),$e=!1,!0):!1}})(),this.connect=a=>{e.domElement=a,e.domElement.style.touchAction="none",e.domElement.addEventListener("contextmenu",Nt),e.domElement.addEventListener("pointerdown",rt),e.domElement.addEventListener("pointercancel",Pe),e.domElement.addEventListener("wheel",oe)},this.dispose=()=>{var a,g,b,R,G,he;e.domElement&&(e.domElement.style.touchAction="auto"),(a=e.domElement)==null||a.removeEventListener("contextmenu",Nt),(g=e.domElement)==null||g.removeEventListener("pointerdown",rt),(b=e.domElement)==null||b.removeEventListener("pointercancel",Pe),(R=e.domElement)==null||R.removeEventListener("wheel",oe),(G=e.domElement)==null||G.ownerDocument.removeEventListener("pointermove",Ve),(he=e.domElement)==null||he.ownerDocument.removeEventListener("pointerup",Pe),e._domElementKeyEvents!==null&&e._domElementKeyEvents.removeEventListener("keydown",wt)};const e=this,r={type:"change"},o={type:"start"},u={type:"end"},c={NONE:-1,ROTATE:0,DOLLY:1,PAN:2,TOUCH_ROTATE:3,TOUCH_PAN:4,TOUCH_DOLLY_PAN:5,TOUCH_DOLLY_ROTATE:6};let l=c.NONE;const p=1e-6,h=new zt,d=new zt;let m=1;const y=new j,P=new X,T=new X,L=new X,S=new X,w=new X,v=new X,M=new X,O=new X,E=new X,te=new j,B=new X;let C=!1;const _=[],A={};function J(){return 2*Math.PI/60/60*e.autoRotateSpeed}function Y(){return Math.pow(.95,e.zoomSpeed)}function de(a){e.reverseOrbit||e.reverseHorizontalOrbit?d.theta+=a:d.theta-=a}function I(a){e.reverseOrbit||e.reverseVerticalOrbit?d.phi+=a:d.phi-=a}const ye=(()=>{const a=new j;return function(b,R){a.setFromMatrixColumn(R,0),a.multiplyScalar(-b),y.add(a)}})(),z=(()=>{const a=new j;return function(b,R){e.screenSpacePanning===!0?a.setFromMatrixColumn(R,1):(a.setFromMatrixColumn(R,0),a.crossVectors(e.object.up,a)),a.multiplyScalar(b),y.add(a)}})(),Z=(()=>{const a=new j;return function(b,R){const G=e.domElement;if(G&&e.object instanceof Qe&&e.object.isPerspectiveCamera){const he=e.object.position;a.copy(he).sub(e.target);let be=a.length();be*=Math.tan(e.object.fov/2*Math.PI/180),ye(2*b*be/G.clientHeight,e.object.matrix),z(2*R*be/G.clientHeight,e.object.matrix)}else G&&e.object instanceof Je&&e.object.isOrthographicCamera?(ye(b*(e.object.right-e.object.left)/e.object.zoom/G.clientWidth,e.object.matrix),z(R*(e.object.top-e.object.bottom)/e.object.zoom/G.clientHeight,e.object.matrix)):(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - pan disabled."),e.enablePan=!1)}})();function ee(a){e.object instanceof Qe&&e.object.isPerspectiveCamera||e.object instanceof Je&&e.object.isOrthographicCamera?m=a:(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled."),e.enableZoom=!1)}function ne(a){ee(m/a)}function Ee(a){ee(m*a)}function fe(a){if(!e.zoomToCursor||!e.domElement)return;C=!0;const g=e.domElement.getBoundingClientRect(),b=a.clientX-g.left,R=a.clientY-g.top,G=g.width,he=g.height;B.x=b/G*2-1,B.y=-(R/he)*2+1,te.set(B.x,B.y,1).unproject(e.object).sub(e.object.position).normalize()}function K(a){return Math.max(e.minDistance,Math.min(e.maxDistance,a))}function Se(a){P.set(a.clientX,a.clientY)}function Ce(a){fe(a),M.set(a.clientX,a.clientY)}function He(a){S.set(a.clientX,a.clientY)}function gt(a){T.set(a.clientX,a.clientY),L.subVectors(T,P).multiplyScalar(e.rotateSpeed);const g=e.domElement;g&&(de(2*Math.PI*L.x/g.clientHeight),I(2*Math.PI*L.y/g.clientHeight)),P.copy(T),e.update()}function ve(a){O.set(a.clientX,a.clientY),E.subVectors(O,M),E.y>0?ne(Y()):E.y<0&&Ee(Y()),M.copy(O),e.update()}function nt(a){w.set(a.clientX,a.clientY),v.subVectors(w,S).multiplyScalar(e.panSpeed),Z(v.x,v.y),S.copy(w),e.update()}function $(a){fe(a),a.deltaY<0?Ee(Y()):a.deltaY>0&&ne(Y()),e.update()}function D(a){let g=!1;switch(a.code){case e.keys.UP:Z(0,e.keyPanSpeed),g=!0;break;case e.keys.BOTTOM:Z(0,-e.keyPanSpeed),g=!0;break;case e.keys.LEFT:Z(e.keyPanSpeed,0),g=!0;break;case e.keys.RIGHT:Z(-e.keyPanSpeed,0),g=!0;break}g&&(a.preventDefault(),e.update())}function se(){if(_.length==1)P.set(_[0].pageX,_[0].pageY);else{const a=.5*(_[0].pageX+_[1].pageX),g=.5*(_[0].pageY+_[1].pageY);P.set(a,g)}}function q(){if(_.length==1)S.set(_[0].pageX,_[0].pageY);else{const a=.5*(_[0].pageX+_[1].pageX),g=.5*(_[0].pageY+_[1].pageY);S.set(a,g)}}function xe(){const a=_[0].pageX-_[1].pageX,g=_[0].pageY-_[1].pageY,b=Math.sqrt(a*a+g*g);M.set(0,b)}function De(){e.enableZoom&&xe(),e.enablePan&&q()}function yt(){e.enableZoom&&xe(),e.enableRotate&&se()}function re(a){if(_.length==1)T.set(a.pageX,a.pageY);else{const b=jt(a),R=.5*(a.pageX+b.x),G=.5*(a.pageY+b.y);T.set(R,G)}L.subVectors(T,P).multiplyScalar(e.rotateSpeed);const g=e.domElement;g&&(de(2*Math.PI*L.x/g.clientHeight),I(2*Math.PI*L.y/g.clientHeight)),P.copy(T)}function Fe(a){if(_.length==1)w.set(a.pageX,a.pageY);else{const g=jt(a),b=.5*(a.pageX+g.x),R=.5*(a.pageY+g.y);w.set(b,R)}v.subVectors(w,S).multiplyScalar(e.panSpeed),Z(v.x,v.y),S.copy(w)}function Ne(a){const g=jt(a),b=a.pageX-g.x,R=a.pageY-g.y,G=Math.sqrt(b*b+R*R);O.set(0,G),E.set(0,Math.pow(O.y/M.y,e.zoomSpeed)),ne(E.y),M.copy(O)}function st(a){e.enableZoom&&Ne(a),e.enablePan&&Fe(a)}function vt(a){e.enableZoom&&Ne(a),e.enableRotate&&re(a)}function rt(a){var g,b;e.enabled!==!1&&(_.length===0&&((g=e.domElement)==null||g.ownerDocument.addEventListener("pointermove",Ve),(b=e.domElement)==null||b.ownerDocument.addEventListener("pointerup",Pe)),An(a),a.pointerType==="touch"?Sn(a):xt(a))}function Ve(a){e.enabled!==!1&&(a.pointerType==="touch"?Pn(a):bt(a))}function Pe(a){var g,b,R;_n(a),_.length===0&&((g=e.domElement)==null||g.releasePointerCapture(a.pointerId),(b=e.domElement)==null||b.ownerDocument.removeEventListener("pointermove",Ve),(R=e.domElement)==null||R.ownerDocument.removeEventListener("pointerup",Pe)),e.dispatchEvent(u),l=c.NONE}function xt(a){let g;switch(a.button){case 0:g=e.mouseButtons.LEFT;break;case 1:g=e.mouseButtons.MIDDLE;break;case 2:g=e.mouseButtons.RIGHT;break;default:g=-1}switch(g){case Ie.DOLLY:if(e.enableZoom===!1)return;Ce(a),l=c.DOLLY;break;case Ie.ROTATE:if(a.ctrlKey||a.metaKey||a.shiftKey){if(e.enablePan===!1)return;He(a),l=c.PAN}else{if(e.enableRotate===!1)return;Se(a),l=c.ROTATE}break;case Ie.PAN:if(a.ctrlKey||a.metaKey||a.shiftKey){if(e.enableRotate===!1)return;Se(a),l=c.ROTATE}else{if(e.enablePan===!1)return;He(a),l=c.PAN}break;default:l=c.NONE}l!==c.NONE&&e.dispatchEvent(o)}function bt(a){if(e.enabled!==!1)switch(l){case c.ROTATE:if(e.enableRotate===!1)return;gt(a);break;case c.DOLLY:if(e.enableZoom===!1)return;ve(a);break;case c.PAN:if(e.enablePan===!1)return;nt(a);break}}function oe(a){e.enabled===!1||e.enableZoom===!1||l!==c.NONE&&l!==c.ROTATE||(a.preventDefault(),e.dispatchEvent(o),$(a),e.dispatchEvent(u))}function wt(a){e.enabled===!1||e.enablePan===!1||D(a)}function Sn(a){switch(It(a),_.length){case 1:switch(e.touches.ONE){case Be.ROTATE:if(e.enableRotate===!1)return;se(),l=c.TOUCH_ROTATE;break;case Be.PAN:if(e.enablePan===!1)return;q(),l=c.TOUCH_PAN;break;default:l=c.NONE}break;case 2:switch(e.touches.TWO){case Be.DOLLY_PAN:if(e.enableZoom===!1&&e.enablePan===!1)return;De(),l=c.TOUCH_DOLLY_PAN;break;case Be.DOLLY_ROTATE:if(e.enableZoom===!1&&e.enableRotate===!1)return;yt(),l=c.TOUCH_DOLLY_ROTATE;break;default:l=c.NONE}break;default:l=c.NONE}l!==c.NONE&&e.dispatchEvent(o)}function Pn(a){switch(It(a),l){case c.TOUCH_ROTATE:if(e.enableRotate===!1)return;re(a),e.update();break;case c.TOUCH_PAN:if(e.enablePan===!1)return;Fe(a),e.update();break;case c.TOUCH_DOLLY_PAN:if(e.enableZoom===!1&&e.enablePan===!1)return;st(a),e.update();break;case c.TOUCH_DOLLY_ROTATE:if(e.enableZoom===!1&&e.enableRotate===!1)return;vt(a),e.update();break;default:l=c.NONE}}function Nt(a){e.enabled!==!1&&a.preventDefault()}function An(a){_.push(a)}function _n(a){delete A[a.pointerId];for(let g=0;g<_.length;g++)if(_[g].pointerId==a.pointerId){_.splice(g,1);return}}function It(a){let g=A[a.pointerId];g===void 0&&(g=new X,A[a.pointerId]=g),g.set(a.pageX,a.pageY)}function jt(a){const g=a.pointerId===_[0].pointerId?_[1]:_[0];return A[g.pointerId]}this.dollyIn=(a=Y())=>{Ee(a),e.update()},this.dollyOut=(a=Y())=>{ne(a),e.update()},this.getScale=()=>m,this.setScale=a=>{ee(a),e.update()},this.getZoomScale=()=>Y(),s!==void 0&&this.connect(s),this.update()}};const $t=new Tt,ct=new j;class Rt extends Cn{constructor(){super(),this.isLineSegmentsGeometry=!0,this.type="LineSegmentsGeometry";const t=[-1,2,0,1,2,0,-1,1,0,1,1,0,-1,0,0,1,0,0,-1,-1,0,1,-1,0],s=[-1,2,1,2,-1,1,1,1,-1,-1,1,-1,-1,-2,1,-2],e=[0,2,1,2,3,1,2,4,3,4,5,3,4,6,5,6,7,5];this.setIndex(e),this.setAttribute("position",new Ut(t,3)),this.setAttribute("uv",new Ut(s,2))}applyMatrix4(t){const s=this.attributes.instanceStart,e=this.attributes.instanceEnd;return s!==void 0&&(s.applyMatrix4(t),e.applyMatrix4(t),s.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this}setPositions(t){let s;t instanceof Float32Array?s=t:Array.isArray(t)&&(s=new Float32Array(t));const e=new _t(s,6,1);return this.setAttribute("instanceStart",new ze(e,3,0)),this.setAttribute("instanceEnd",new ze(e,3,3)),this.computeBoundingBox(),this.computeBoundingSphere(),this}setColors(t,s=3){let e;t instanceof Float32Array?e=t:Array.isArray(t)&&(e=new Float32Array(t));const r=new _t(e,s*2,1);return this.setAttribute("instanceColorStart",new ze(r,s,0)),this.setAttribute("instanceColorEnd",new ze(r,s,s)),this}fromWireframeGeometry(t){return this.setPositions(t.attributes.position.array),this}fromEdgesGeometry(t){return this.setPositions(t.attributes.position.array),this}fromMesh(t){return this.fromWireframeGeometry(new Dn(t.geometry)),this}fromLineSegments(t){const s=t.geometry;return this.setPositions(s.attributes.position.array),this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new Tt);const t=this.attributes.instanceStart,s=this.attributes.instanceEnd;t!==void 0&&s!==void 0&&(this.boundingBox.setFromBufferAttribute(t),$t.setFromBufferAttribute(s),this.boundingBox.union($t))}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new cn),this.boundingBox===null&&this.computeBoundingBox();const t=this.attributes.instanceStart,s=this.attributes.instanceEnd;if(t!==void 0&&s!==void 0){const e=this.boundingSphere.center;this.boundingBox.getCenter(e);let r=0;for(let o=0,u=t.count;o<u;o++)ct.fromBufferAttribute(t,o),r=Math.max(r,e.distanceToSquared(ct)),ct.fromBufferAttribute(s,o),r=Math.max(r,e.distanceToSquared(ct));this.boundingSphere.radius=Math.sqrt(r),isNaN(this.boundingSphere.radius)&&console.error("THREE.LineSegmentsGeometry.computeBoundingSphere(): Computed radius is NaN. The instanced position data is likely to have NaN values.",this)}}toJSON(){}applyMatrix(t){return console.warn("THREE.LineSegmentsGeometry: applyMatrix() has been renamed to applyMatrix4()."),this.applyMatrix4(t)}}class pn extends Rt{constructor(){super(),this.isLineGeometry=!0,this.type="LineGeometry"}setPositions(t){const s=t.length-3,e=new Float32Array(2*s);for(let r=0;r<s;r+=3)e[2*r]=t[r],e[2*r+1]=t[r+1],e[2*r+2]=t[r+2],e[2*r+3]=t[r+3],e[2*r+4]=t[r+4],e[2*r+5]=t[r+5];return super.setPositions(e),this}setColors(t,s=3){const e=t.length-s,r=new Float32Array(2*e);if(s===3)for(let o=0;o<e;o+=s)r[2*o]=t[o],r[2*o+1]=t[o+1],r[2*o+2]=t[o+2],r[2*o+3]=t[o+3],r[2*o+4]=t[o+4],r[2*o+5]=t[o+5];else for(let o=0;o<e;o+=s)r[2*o]=t[o],r[2*o+1]=t[o+1],r[2*o+2]=t[o+2],r[2*o+3]=t[o+3],r[2*o+4]=t[o+4],r[2*o+5]=t[o+5],r[2*o+6]=t[o+6],r[2*o+7]=t[o+7];return super.setColors(r,s),this}fromLine(t){const s=t.geometry;return this.setPositions(s.attributes.position.array),this}}class Ct extends ln{constructor(t){super({type:"LineMaterial",uniforms:kt.clone(kt.merge([Wt.common,Wt.fog,{worldUnits:{value:1},linewidth:{value:1},resolution:{value:new X(1,1)},dashOffset:{value:0},dashScale:{value:1},dashSize:{value:1},gapSize:{value:1}}])),vertexShader:`
				#include <common>
				#include <fog_pars_vertex>
				#include <logdepthbuf_pars_vertex>
				#include <clipping_planes_pars_vertex>

				uniform float linewidth;
				uniform vec2 resolution;

				attribute vec3 instanceStart;
				attribute vec3 instanceEnd;

				#ifdef USE_COLOR
					#ifdef USE_LINE_COLOR_ALPHA
						varying vec4 vLineColor;
						attribute vec4 instanceColorStart;
						attribute vec4 instanceColorEnd;
					#else
						varying vec3 vLineColor;
						attribute vec3 instanceColorStart;
						attribute vec3 instanceColorEnd;
					#endif
				#endif

				#ifdef WORLD_UNITS

					varying vec4 worldPos;
					varying vec3 worldStart;
					varying vec3 worldEnd;

					#ifdef USE_DASH

						varying vec2 vUv;

					#endif

				#else

					varying vec2 vUv;

				#endif

				#ifdef USE_DASH

					uniform float dashScale;
					attribute float instanceDistanceStart;
					attribute float instanceDistanceEnd;
					varying float vLineDistance;

				#endif

				void trimSegment( const in vec4 start, inout vec4 end ) {

					// trim end segment so it terminates between the camera plane and the near plane

					// conservative estimate of the near plane
					float a = projectionMatrix[ 2 ][ 2 ]; // 3nd entry in 3th column
					float b = projectionMatrix[ 3 ][ 2 ]; // 3nd entry in 4th column
					float nearEstimate = - 0.5 * b / a;

					float alpha = ( nearEstimate - start.z ) / ( end.z - start.z );

					end.xyz = mix( start.xyz, end.xyz, alpha );

				}

				void main() {

					#ifdef USE_COLOR

						vLineColor = ( position.y < 0.5 ) ? instanceColorStart : instanceColorEnd;

					#endif

					#ifdef USE_DASH

						vLineDistance = ( position.y < 0.5 ) ? dashScale * instanceDistanceStart : dashScale * instanceDistanceEnd;
						vUv = uv;

					#endif

					float aspect = resolution.x / resolution.y;

					// camera space
					vec4 start = modelViewMatrix * vec4( instanceStart, 1.0 );
					vec4 end = modelViewMatrix * vec4( instanceEnd, 1.0 );

					#ifdef WORLD_UNITS

						worldStart = start.xyz;
						worldEnd = end.xyz;

					#else

						vUv = uv;

					#endif

					// special case for perspective projection, and segments that terminate either in, or behind, the camera plane
					// clearly the gpu firmware has a way of addressing this issue when projecting into ndc space
					// but we need to perform ndc-space calculations in the shader, so we must address this issue directly
					// perhaps there is a more elegant solution -- WestLangley

					bool perspective = ( projectionMatrix[ 2 ][ 3 ] == - 1.0 ); // 4th entry in the 3rd column

					if ( perspective ) {

						if ( start.z < 0.0 && end.z >= 0.0 ) {

							trimSegment( start, end );

						} else if ( end.z < 0.0 && start.z >= 0.0 ) {

							trimSegment( end, start );

						}

					}

					// clip space
					vec4 clipStart = projectionMatrix * start;
					vec4 clipEnd = projectionMatrix * end;

					// ndc space
					vec3 ndcStart = clipStart.xyz / clipStart.w;
					vec3 ndcEnd = clipEnd.xyz / clipEnd.w;

					// direction
					vec2 dir = ndcEnd.xy - ndcStart.xy;

					// account for clip-space aspect ratio
					dir.x *= aspect;
					dir = normalize( dir );

					#ifdef WORLD_UNITS

						// get the offset direction as perpendicular to the view vector
						vec3 worldDir = normalize( end.xyz - start.xyz );
						vec3 offset;
						if ( position.y < 0.5 ) {

							offset = normalize( cross( start.xyz, worldDir ) );

						} else {

							offset = normalize( cross( end.xyz, worldDir ) );

						}

						// sign flip
						if ( position.x < 0.0 ) offset *= - 1.0;

						float forwardOffset = dot( worldDir, vec3( 0.0, 0.0, 1.0 ) );

						// don't extend the line if we're rendering dashes because we
						// won't be rendering the endcaps
						#ifndef USE_DASH

							// extend the line bounds to encompass  endcaps
							start.xyz += - worldDir * linewidth * 0.5;
							end.xyz += worldDir * linewidth * 0.5;

							// shift the position of the quad so it hugs the forward edge of the line
							offset.xy -= dir * forwardOffset;
							offset.z += 0.5;

						#endif

						// endcaps
						if ( position.y > 1.0 || position.y < 0.0 ) {

							offset.xy += dir * 2.0 * forwardOffset;

						}

						// adjust for linewidth
						offset *= linewidth * 0.5;

						// set the world position
						worldPos = ( position.y < 0.5 ) ? start : end;
						worldPos.xyz += offset;

						// project the worldpos
						vec4 clip = projectionMatrix * worldPos;

						// shift the depth of the projected points so the line
						// segments overlap neatly
						vec3 clipPose = ( position.y < 0.5 ) ? ndcStart : ndcEnd;
						clip.z = clipPose.z * clip.w;

					#else

						vec2 offset = vec2( dir.y, - dir.x );
						// undo aspect ratio adjustment
						dir.x /= aspect;
						offset.x /= aspect;

						// sign flip
						if ( position.x < 0.0 ) offset *= - 1.0;

						// endcaps
						if ( position.y < 0.0 ) {

							offset += - dir;

						} else if ( position.y > 1.0 ) {

							offset += dir;

						}

						// adjust for linewidth
						offset *= linewidth;

						// adjust for clip-space to screen-space conversion // maybe resolution should be based on viewport ...
						offset /= resolution.y;

						// select end
						vec4 clip = ( position.y < 0.5 ) ? clipStart : clipEnd;

						// back to clip space
						offset *= clip.w;

						clip.xy += offset;

					#endif

					gl_Position = clip;

					vec4 mvPosition = ( position.y < 0.5 ) ? start : end; // this is an approximation

					#include <logdepthbuf_vertex>
					#include <clipping_planes_vertex>
					#include <fog_vertex>

				}
			`,fragmentShader:`
				uniform vec3 diffuse;
				uniform float opacity;
				uniform float linewidth;

				#ifdef USE_DASH

					uniform float dashOffset;
					uniform float dashSize;
					uniform float gapSize;

				#endif

				varying float vLineDistance;

				#ifdef WORLD_UNITS

					varying vec4 worldPos;
					varying vec3 worldStart;
					varying vec3 worldEnd;

					#ifdef USE_DASH

						varying vec2 vUv;

					#endif

				#else

					varying vec2 vUv;

				#endif

				#include <common>
				#include <fog_pars_fragment>
				#include <logdepthbuf_pars_fragment>
				#include <clipping_planes_pars_fragment>

				#ifdef USE_COLOR
					#ifdef USE_LINE_COLOR_ALPHA
						varying vec4 vLineColor;
					#else
						varying vec3 vLineColor;
					#endif
				#endif

				vec2 closestLineToLine(vec3 p1, vec3 p2, vec3 p3, vec3 p4) {

					float mua;
					float mub;

					vec3 p13 = p1 - p3;
					vec3 p43 = p4 - p3;

					vec3 p21 = p2 - p1;

					float d1343 = dot( p13, p43 );
					float d4321 = dot( p43, p21 );
					float d1321 = dot( p13, p21 );
					float d4343 = dot( p43, p43 );
					float d2121 = dot( p21, p21 );

					float denom = d2121 * d4343 - d4321 * d4321;

					float numer = d1343 * d4321 - d1321 * d4343;

					mua = numer / denom;
					mua = clamp( mua, 0.0, 1.0 );
					mub = ( d1343 + d4321 * ( mua ) ) / d4343;
					mub = clamp( mub, 0.0, 1.0 );

					return vec2( mua, mub );

				}

				void main() {

					#include <clipping_planes_fragment>

					#ifdef USE_DASH

						if ( vUv.y < - 1.0 || vUv.y > 1.0 ) discard; // discard endcaps

						if ( mod( vLineDistance + dashOffset, dashSize + gapSize ) > dashSize ) discard; // todo - FIX

					#endif

					float alpha = opacity;

					#ifdef WORLD_UNITS

						// Find the closest points on the view ray and the line segment
						vec3 rayEnd = normalize( worldPos.xyz ) * 1e5;
						vec3 lineDir = worldEnd - worldStart;
						vec2 params = closestLineToLine( worldStart, worldEnd, vec3( 0.0, 0.0, 0.0 ), rayEnd );

						vec3 p1 = worldStart + lineDir * params.x;
						vec3 p2 = rayEnd * params.y;
						vec3 delta = p1 - p2;
						float len = length( delta );
						float norm = len / linewidth;

						#ifndef USE_DASH

							#ifdef USE_ALPHA_TO_COVERAGE

								float dnorm = fwidth( norm );
								alpha = 1.0 - smoothstep( 0.5 - dnorm, 0.5 + dnorm, norm );

							#else

								if ( norm > 0.5 ) {

									discard;

								}

							#endif

						#endif

					#else

						#ifdef USE_ALPHA_TO_COVERAGE

							// artifacts appear on some hardware if a derivative is taken within a conditional
							float a = vUv.x;
							float b = ( vUv.y > 0.0 ) ? vUv.y - 1.0 : vUv.y + 1.0;
							float len2 = a * a + b * b;
							float dlen = fwidth( len2 );

							if ( abs( vUv.y ) > 1.0 ) {

								alpha = 1.0 - smoothstep( 1.0 - dlen, 1.0 + dlen, len2 );

							}

						#else

							if ( abs( vUv.y ) > 1.0 ) {

								float a = vUv.x;
								float b = ( vUv.y > 0.0 ) ? vUv.y - 1.0 : vUv.y + 1.0;
								float len2 = a * a + b * b;

								if ( len2 > 1.0 ) discard;

							}

						#endif

					#endif

					vec4 diffuseColor = vec4( diffuse, alpha );
					#ifdef USE_COLOR
						#ifdef USE_LINE_COLOR_ALPHA
							diffuseColor *= vLineColor;
						#else
							diffuseColor.rgb *= vLineColor;
						#endif
					#endif

					#include <logdepthbuf_fragment>

					gl_FragColor = diffuseColor;

					#include <tonemapping_fragment>
					#include <${an>=154?"colorspace_fragment":"encodings_fragment"}>
					#include <fog_fragment>
					#include <premultiplied_alpha_fragment>

				}
			`,clipping:!0}),this.isLineMaterial=!0,this.onBeforeCompile=function(){this.transparent?this.defines.USE_LINE_COLOR_ALPHA="1":delete this.defines.USE_LINE_COLOR_ALPHA},Object.defineProperties(this,{color:{enumerable:!0,get:function(){return this.uniforms.diffuse.value},set:function(s){this.uniforms.diffuse.value=s}},worldUnits:{enumerable:!0,get:function(){return"WORLD_UNITS"in this.defines},set:function(s){s===!0?this.defines.WORLD_UNITS="":delete this.defines.WORLD_UNITS}},linewidth:{enumerable:!0,get:function(){return this.uniforms.linewidth.value},set:function(s){this.uniforms.linewidth.value=s}},dashed:{enumerable:!0,get:function(){return"USE_DASH"in this.defines},set(s){!!s!="USE_DASH"in this.defines&&(this.needsUpdate=!0),s===!0?this.defines.USE_DASH="":delete this.defines.USE_DASH}},dashScale:{enumerable:!0,get:function(){return this.uniforms.dashScale.value},set:function(s){this.uniforms.dashScale.value=s}},dashSize:{enumerable:!0,get:function(){return this.uniforms.dashSize.value},set:function(s){this.uniforms.dashSize.value=s}},dashOffset:{enumerable:!0,get:function(){return this.uniforms.dashOffset.value},set:function(s){this.uniforms.dashOffset.value=s}},gapSize:{enumerable:!0,get:function(){return this.uniforms.gapSize.value},set:function(s){this.uniforms.gapSize.value=s}},opacity:{enumerable:!0,get:function(){return this.uniforms.opacity.value},set:function(s){this.uniforms.opacity.value=s}},resolution:{enumerable:!0,get:function(){return this.uniforms.resolution.value},set:function(s){this.uniforms.resolution.value.copy(s)}},alphaToCoverage:{enumerable:!0,get:function(){return"USE_ALPHA_TO_COVERAGE"in this.defines},set:function(s){!!s!="USE_ALPHA_TO_COVERAGE"in this.defines&&(this.needsUpdate=!0),s===!0?(this.defines.USE_ALPHA_TO_COVERAGE="",this.extensions.derivatives=!0):(delete this.defines.USE_ALPHA_TO_COVERAGE,this.extensions.derivatives=!1)}}}),this.setValues(t)}}const Mt=new ke,Yt=new j,Xt=new j,k=new ke,W=new ke,ie=new ke,Et=new j,St=new Bn,H=new In,Zt=new j,lt=new Tt,ut=new cn,ae=new ke;let ce,_e;function Kt(n,t,s){return ae.set(0,0,-t,1).applyMatrix4(n.projectionMatrix),ae.multiplyScalar(1/ae.w),ae.x=_e/s.width,ae.y=_e/s.height,ae.applyMatrix4(n.projectionMatrixInverse),ae.multiplyScalar(1/ae.w),Math.abs(Math.max(ae.x,ae.y))}function us(n,t){const s=n.matrixWorld,e=n.geometry,r=e.attributes.instanceStart,o=e.attributes.instanceEnd,u=Math.min(e.instanceCount,r.count);for(let c=0,l=u;c<l;c++){H.start.fromBufferAttribute(r,c),H.end.fromBufferAttribute(o,c),H.applyMatrix4(s);const p=new j,h=new j;ce.distanceSqToSegment(H.start,H.end,h,p),h.distanceTo(p)<_e*.5&&t.push({point:h,pointOnLine:p,distance:ce.origin.distanceTo(h),object:n,face:null,faceIndex:c,uv:null,[hn]:null})}}function ds(n,t,s){const e=t.projectionMatrix,o=n.material.resolution,u=n.matrixWorld,c=n.geometry,l=c.attributes.instanceStart,p=c.attributes.instanceEnd,h=Math.min(c.instanceCount,l.count),d=-t.near;ce.at(1,ie),ie.w=1,ie.applyMatrix4(t.matrixWorldInverse),ie.applyMatrix4(e),ie.multiplyScalar(1/ie.w),ie.x*=o.x/2,ie.y*=o.y/2,ie.z=0,Et.copy(ie),St.multiplyMatrices(t.matrixWorldInverse,u);for(let m=0,y=h;m<y;m++){if(k.fromBufferAttribute(l,m),W.fromBufferAttribute(p,m),k.w=1,W.w=1,k.applyMatrix4(St),W.applyMatrix4(St),k.z>d&&W.z>d)continue;if(k.z>d){const v=k.z-W.z,M=(k.z-d)/v;k.lerp(W,M)}else if(W.z>d){const v=W.z-k.z,M=(W.z-d)/v;W.lerp(k,M)}k.applyMatrix4(e),W.applyMatrix4(e),k.multiplyScalar(1/k.w),W.multiplyScalar(1/W.w),k.x*=o.x/2,k.y*=o.y/2,W.x*=o.x/2,W.y*=o.y/2,H.start.copy(k),H.start.z=0,H.end.copy(W),H.end.z=0;const T=H.closestPointToPointParameter(Et,!0);H.at(T,Zt);const L=zn.lerp(k.z,W.z,T),S=L>=-1&&L<=1,w=Et.distanceTo(Zt)<_e*.5;if(S&&w){H.start.fromBufferAttribute(l,m),H.end.fromBufferAttribute(p,m),H.start.applyMatrix4(u),H.end.applyMatrix4(u);const v=new j,M=new j;ce.distanceSqToSegment(H.start,H.end,M,v),s.push({point:M,pointOnLine:v,distance:ce.origin.distanceTo(M),object:n,face:null,faceIndex:m,uv:null,[hn]:null})}}}class mn extends Nn{constructor(t=new Rt,s=new Ct({color:Math.random()*16777215})){super(t,s),this.isLineSegments2=!0,this.type="LineSegments2"}computeLineDistances(){const t=this.geometry,s=t.attributes.instanceStart,e=t.attributes.instanceEnd,r=new Float32Array(2*s.count);for(let u=0,c=0,l=s.count;u<l;u++,c+=2)Yt.fromBufferAttribute(s,u),Xt.fromBufferAttribute(e,u),r[c]=c===0?0:r[c-1],r[c+1]=r[c]+Yt.distanceTo(Xt);const o=new _t(r,2,1);return t.setAttribute("instanceDistanceStart",new ze(o,1,0)),t.setAttribute("instanceDistanceEnd",new ze(o,1,1)),this}raycast(t,s){const e=this.material.worldUnits,r=t.camera;r===null&&!e&&console.error('LineSegments2: "Raycaster.camera" needs to be set in order to raycast against LineSegments2 while worldUnits is set to false.');const o=t.params.Line2!==void 0&&t.params.Line2.threshold||0;ce=t.ray;const u=this.matrixWorld,c=this.geometry,l=this.material;_e=l.linewidth+o,c.boundingSphere===null&&c.computeBoundingSphere(),ut.copy(c.boundingSphere).applyMatrix4(u);let p;if(e)p=_e*.5;else{const d=Math.max(r.near,ut.distanceToPoint(ce.origin));p=Kt(r,d,l.resolution)}if(ut.radius+=p,ce.intersectsSphere(ut)===!1)return;c.boundingBox===null&&c.computeBoundingBox(),lt.copy(c.boundingBox).applyMatrix4(u);let h;if(e)h=_e*.5;else{const d=Math.max(r.near,lt.distanceToPoint(ce.origin));h=Kt(r,d,l.resolution)}lt.expandByScalar(h),ce.intersectsBox(lt)!==!1&&(e?us(this,s):ds(this,r,s))}onBeforeRender(t){const s=this.material.uniforms;s&&s.resolution&&(t.getViewport(Mt),this.material.uniforms.resolution.value.set(Mt.z,Mt.w))}}class fs extends mn{constructor(t=new pn,s=new Ct({color:Math.random()*16777215})){super(t,s),this.isLine2=!0,this.type="Line2"}}const Me=f.forwardRef(function({points:t,color:s=16777215,vertexColors:e,linewidth:r,lineWidth:o,segments:u,dashed:c,...l},p){var h,d;const m=Q(S=>S.size),y=f.useMemo(()=>u?new mn:new fs,[u]),[P]=f.useState(()=>new Ct),T=(e==null||(h=e[0])==null?void 0:h.length)===4?4:3,L=f.useMemo(()=>{const S=u?new Rt:new pn,w=t.map(v=>{const M=Array.isArray(v);return v instanceof j||v instanceof ke?[v.x,v.y,v.z]:v instanceof X?[v.x,v.y,0]:M&&v.length===3?[v[0],v[1],v[2]]:M&&v.length===2?[v[0],v[1],0]:v});if(S.setPositions(w.flat()),e){s=16777215;const v=e.map(M=>M instanceof je?M.toArray():M);S.setColors(v.flat(),T)}return S},[t,u,e,T]);return f.useLayoutEffect(()=>{y.computeLineDistances()},[t,y]),f.useLayoutEffect(()=>{c?P.defines.USE_DASH="":delete P.defines.USE_DASH,P.needsUpdate=!0},[c,P]),f.useEffect(()=>()=>{L.dispose(),P.dispose()},[L]),f.createElement("primitive",Le({object:y,ref:p},l),f.createElement("primitive",{object:L,attach:"geometry"}),f.createElement("primitive",Le({object:P,attach:"material",color:s,vertexColors:!!e,resolution:[m.width,m.height],linewidth:(d=r??o)!==null&&d!==void 0?d:1,dashed:c,transparent:T===4},l)))}),hs=new j,ps=f.forwardRef(function({start:t=[0,0,0],end:s=[0,0,0],mid:e,segments:r=20,...o},u){const c=f.useRef(null);f.useImperativeHandle(u,()=>c.current);const[l]=f.useState(()=>new Gn(void 0,void 0,void 0)),p=f.useCallback((d,m,y,P=20)=>(d instanceof j?l.v0.copy(d):l.v0.set(...d),m instanceof j?l.v2.copy(m):l.v2.set(...m),y instanceof j?l.v1.copy(y):Array.isArray(y)?l.v1.set(...y):l.v1.copy(l.v0.clone().add(l.v2.clone().sub(l.v0)).add(hs.set(0,l.v0.y-l.v2.y,0))),l.getPoints(P)),[]);f.useLayoutEffect(()=>{c.current.setPoints=(d,m,y)=>{const P=p(d,m,y);c.current.geometry&&c.current.geometry.setPositions(P.map(T=>T.toArray()).flat())}},[]);const h=f.useMemo(()=>p(t,s,e,r),[t,s,e,r]);return f.createElement(Me,Le({ref:c,points:h},o))}),ms=f.forwardRef(({makeDefault:n,camera:t,regress:s,domElement:e,enableDamping:r=!0,keyEvents:o=!1,onChange:u,onStart:c,onEnd:l,...p},h)=>{const d=Q(E=>E.invalidate),m=Q(E=>E.camera),y=Q(E=>E.gl),P=Q(E=>E.events),T=Q(E=>E.setEvents),L=Q(E=>E.set),S=Q(E=>E.get),w=Q(E=>E.performance),v=t||m,M=e||P.connected||y.domElement,O=f.useMemo(()=>new ls(v),[v]);return U(()=>{O.enabled&&O.update()},-1),f.useEffect(()=>(o&&O.connect(o===!0?M:o),O.connect(M),()=>void O.dispose()),[o,M,s,O,d]),f.useEffect(()=>{const E=C=>{d(),s&&w.regress(),u&&u(C)},te=C=>{c&&c(C)},B=C=>{l&&l(C)};return O.addEventListener("change",E),O.addEventListener("start",te),O.addEventListener("end",B),()=>{O.removeEventListener("start",te),O.removeEventListener("end",B),O.removeEventListener("change",E)}},[u,c,l,O,d,T]),f.useEffect(()=>{if(n){const E=S().controls;return L({controls:O}),()=>L({controls:E})}},[n,O]),f.createElement("primitive",Le({ref:h,object:O,enableDamping:r},p))}),V={"CHN-01":{name:"Park Town",pos:[.6,0,-1.6]},"CHN-02":{name:"T. Nagar",pos:[-.9,0,.1]},"CHN-03":{name:"Adyar",pos:[.5,0,1.6]},"CHN-04":{name:"Guindy",pos:[-1,0,1.5]},"CHN-05":{name:"Ennore",pos:[1.3,0,-3.1]},"CHN-06":{name:"OMR",pos:[1.5,0,2.9]}},F={"GW-IN-1":{name:"GW-IN-1 Chennai",pos:[-2.6,0,-1.2]},"GW-IN-2":{name:"GW-IN-2 Bengaluru",pos:[-5.2,0,1.4]},"GW-XX":{name:"GW-XX foreign",pos:[5.6,0,-3.8],foreign:!0}},le=[-.6,5.2,-.4],ue=[-4,0,-2.7],gs=[-6.6,0,-4.4],ys=new Set(["mgmt_intrusion","failover_lure","telemetry_edit","ss7_abuse","firmware_exploit"]),gn=n=>ys.has(n),Ue=n=>n?V[n]?V[n].pos:F[n]?F[n].pos:n==="SAT-MGMT"?ue:null:null,yn=(n,t)=>{if(gn(n))return gs;const s=Ue(t)??[2.8,0,-.6];return[s[0]+1.6,0,s[2]-1.4]},Dt=(n,t)=>t==="ok"?n.ok:t==="warn"?n.warn:t==="critical"?n.critical:t==="healing"?n.healing:t==="accent"?n.accent:n.unknown,Pt="#9B7BE0",At={mobile_operator:"#5B8DEF",satellite_operator:"#3FB5C9",power_utility:"#D9B341",cert_in:"#E08A4F",regulator:"#A77BD9",gap_analyst:"#4FB58A"},dt=["mobile_operator","satellite_operator","power_utility","cert_in","regulator","gap_analyst"],vs={mobile_operator:"Mobile op",satellite_operator:"Sat op",power_utility:"Power",cert_in:"CERT-In",regulator:"Regulator",gap_analyst:"Gap analyst"},Oe=[-2.6,2.9,-1.2],Ke=[ue[0],2.2,ue[2]],vn=[0,2.2,0],xs=Object.fromEntries(on.filter(n=>n.id.startsWith("gap:")).map(n=>[n.id,n.label])),xn={kind:"idle",node:"sat",tone:"ok"};function Ze(n){return n.startsWith("threat:")?"threat":n.startsWith("model:")?"detect":n.startsWith("agent:")?"coordinate":n==="rules"||n==="clocks"?"rules":n==="human"?"commander":n.startsWith("exec:")?"heal":n.startsWith("gap:")?"gap":"idle"}const bn=/(CHN-0[1-6]|GW-IN-[12]|SAT-MGMT)/,Ge=n=>{var t;return n?(t=bn.exec(n))==null?void 0:t[1]:void 0},qt=n=>n.startsWith("site:")?n.slice(5):n.startsWith("gw:")&&n!=="gw:GW-XX"?n.slice(3):n==="mgmt"?"SAT-MGMT":void 0;function bs(n,t){if(t)return t;let s;for(const[e,r]of Object.entries(n))if(!(!e.startsWith("site:")||r.word==="OK"||!r.word)){if(r.phase==="active")return e.slice(5);s??(s=e.slice(5))}return s}function ws(n,t,s,e){var o,u;const r=s[t];if(n==="detect"){const c=t.slice(6),l=(r==null?void 0:r.word)??"";if(c==="M1")return`M1 ${((o=/score ([\d.]+)/.exec((r==null?void 0:r.detail)??""))==null?void 0:o[1])??""} ${l}`.replace(/\s+/g," ").trim();if(c==="M3"){const p=(u=/([\d.]+)$/.exec((r==null?void 0:r.detail)??""))==null?void 0:u[1];return`M3 ${l}${p&&l!=="UNSURE"?` ${p}`:""}`}return c==="M2"?`M2 ${l}${r!=null&&r.detail?` · ${(r.detail??"").replace(bn,"").trim()}`:""}`:`${c} ${l}`}return n==="rules"?t==="clocks"?`Clock ${(r==null?void 0:r.detail)??""}`.trim():`Rules ${(r==null?void 0:r.word)??""}`.trim():n==="commander"?r!=null&&r.word?r.word:"Commander":n==="threat"?e==null?void 0:e.title:n==="gap"?`Gap ${t.slice(-2)}: ${xs[t]??"policy gap"}`:e==null?void 0:e.title}function js(n,t,s,e){let r=(n==null?void 0:n.node)??"sat",o=Ze(r),u=(n==null?void 0:n.tone)??"ok",c;if(t){const d=Ze(t.to),m=Ze(t.from),y=d!=="idle"?t.to:t.from;o=d!=="idle"?d:m,m==="threat"?(o="threat",r=t.from):r=y,u=t.tone,c=qt(t.from)??qt(t.to),o==="idle"&&(o=Ze(r))}if(o==="idle")return{...xn,tone:u};const l=n&&Ze(n.node)===o,p=s[r],h=Ge(l?n==null?void 0:n.text:void 0)??c??Ge(p==null?void 0:p.detail)??Ge(n==null?void 0:n.text)??bs(s,e)??(o==="rules"||o==="threat"?"SAT-MGMT":void 0);return{kind:o,site:h,node:r,label:ws(o,r,s,l?n:void 0),tone:l?n.tone:u}}const wn=n=>{var t,s;return((s=/(GW-IN-[12]|GW-XX)/.exec(((t=n["exec:cleanpath"])==null?void 0:t.detail)??""))==null?void 0:s[1])??"GW-IN-2"},Ms=n=>{var t,s,e;return Ge((t=n["exec:failover"])==null?void 0:t.detail)??Ge((s=n["exec:reattack"])==null?void 0:s.detail)??Ge((e=n["exec:clone"])==null?void 0:e.detail)},Qt=[7.5,7.2,6.5];function Es(n,t){var r;const s=Ue(n.site),e=o=>s?[s[0],o,s[2]]:[0,o,0];switch(n.kind){case"threat":return n.site==="SAT-MGMT"?{target:[Ke[0],1.2,Ke[2]],offset:[4.2,3.2,4.6]}:{target:e(.9),offset:[3.3,2.7,3.6]};case"detect":return{target:e(.9),offset:[3.8,3.2,4]};case"coordinate":return{target:[Oe[0],Oe[1]-.5,Oe[2]],offset:[4.6,2.6,5.2]};case"rules":return{target:[Ke[0],1.4,Ke[2]],offset:[4.2,2.8,4.6]};case"commander":return{target:[0,1,0],offset:[9.5,9,8.5]};case"gap":return{target:[-1,.6,0],offset:[8,7.5,7]};case"heal":{const o=n.node.slice(5);if(o==="r5"||o==="r25"||o==="r100")return{target:[-.4,2.2,-.6],offset:[7.5,5,7]};if(o==="cleanpath"||o==="failover"){const u=((r=F[wn(t)])==null?void 0:r.pos)??F["GW-IN-2"].pos,c=s??V["CHN-01"].pos;return{target:[(c[0]+u[0])/2,1,(c[2]+u[2])/2],offset:[6,5,6]}}return{target:e(.9),offset:[4,3.4,4.2]}}default:return null}}const et=n=>{const t=Math.min(1,Math.max(0,n));return t*t*(3-2*t)},ge=n=>Math.min(1,Math.max(0,n)),Ss="varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",Ps=`
varying vec2 vUv;
uniform vec3 uColor; uniform float uProgress; uniform float uTime; uniform float uAlpha; uniform float uDash; uniform float uSolid;
void main(){
  if (vUv.x > uProgress) discard;
  float d = fract(vUv.x * uDash - uTime);
  float dash = smoothstep(0.0, 0.1, d) * (1.0 - smoothstep(0.5, 0.62, d));
  float head = smoothstep(0.1, 0.0, uProgress - vUv.x);
  float a = mix(0.18 + 0.82 * dash, 1.0, uSolid) * 0.9 + head;
  gl_FragColor = vec4(uColor * (1.0 + head * 0.8), clamp(a, 0.0, 1.0) * uAlpha);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;function pt({curve:n,color:t,radius:s=.035,dash:e=14,speed:r=2.2,solid:o=0,progress:u,alpha:c,ctx:l}){const p=f.useMemo(()=>new kn(n,56,s,6,!1),[n,s]);f.useEffect(()=>()=>p.dispose(),[p]);const h=f.useMemo(()=>new ln({vertexShader:Ss,fragmentShader:Ps,transparent:!0,depthWrite:!1,blending:Wn,uniforms:{uColor:{value:new je(t)},uProgress:{value:1},uTime:{value:0},uAlpha:{value:1},uDash:{value:e},uSolid:{value:o}}}),[]);return f.useEffect(()=>{h.uniforms.uColor.value.set(t),h.uniforms.uDash.value=e,h.uniforms.uSolid.value=o},[h,t,e,o]),f.useEffect(()=>()=>h.dispose(),[h]),U(()=>{const d=u===void 0?1:typeof u=="function"?u():u.current;h.uniforms.uProgress.value=l.reduced?1:d,h.uniforms.uTime.value=l.reduced?0:l.time.current*r,h.uniforms.uAlpha.value=(c===void 0?1:typeof c=="number"?c:c.current)*l.alpha.current}),i.jsx("mesh",{geometry:p,material:h,frustumCulled:!1,renderOrder:5})}function jn(n,t=.5){const s=[];return n.forEach((e,r)=>{if(r>0){const o=n[r-1];s.push(new j((o[0]+e[0])/2,Math.max(o[1],e[1])+t,(o[2]+e[2])/2))}s.push(new j(...e))}),new Un(s,!1,"catmullrom",.3)}function We({position:n,text:t,tone:s,ctx:e,keep:r,sub:o}){const u=f.useRef(null);return U(()=>{u.current&&(u.current.style.opacity=String(r?1:e.alpha.current))}),i.jsx(Re,{position:n,center:!0,zIndexRange:[30,0],style:{pointerEvents:"none"},children:i.jsxs("div",{ref:u,className:"scn-holo","data-tone":s,children:[i.jsx("b",{children:t}),o?i.jsx("span",{children:o}):null]})})}const N=(n,t=1,s={})=>({color:n,transparent:!0,opacity:t,depthWrite:!1,toneMapped:!1,...s});function As({ctx:n,nodes:t,pending:s}){const e=t.human,r=(e==null?void 0:e.word)==="APPROVED"||(e==null?void 0:e.word)==="AUTO",o=(e==null?void 0:e.word)==="REJECTED",u=f.useRef(null),c=f.useRef(null),l=f.useRef(null),p=f.useRef(0),h=f.useRef(!1),d=new je(n.palette.accent),m=new je(n.palette.ok),y=new je(n.palette.critical);U((T,L)=>{const S=s?1:n.alpha.current;r&&!h.current&&(p.current=1),h.current=r,p.current=Math.max(0,p.current-L*1.1);const w=r?m:o?y:d;for(const O of[u.current,c.current])O&&O.material.color.lerp(w,1-Math.exp(-L*6));const M=1+(n.reduced?0:.04*Math.sin(n.time.current*(s?3:1.5)))+(n.reduced?0:.35*Math.sin(Math.PI*(1-p.current))*(p.current>0?1:0));l.current&&(l.current.scale.setScalar(M),n.reduced||(l.current.rotation.y+=L*.3),l.current.visible=S>.01),u.current&&(u.current.material.opacity=(.08+.18*p.current)*S),c.current&&(c.current.material.opacity=(.55+.4*p.current)*S)});const P=e!=null&&e.word?e.word:"COMMANDER";return i.jsxs("group",{position:vn,children:[i.jsxs("group",{ref:l,children:[i.jsxs("mesh",{ref:u,children:[i.jsx("icosahedronGeometry",{args:[.75,1]}),i.jsx("meshBasicMaterial",{...N(n.palette.accent,.1)})]}),i.jsxs("mesh",{ref:c,children:[i.jsx("icosahedronGeometry",{args:[.78,1]}),i.jsx("meshBasicMaterial",{...N(n.palette.accent,.6,{wireframe:!0})})]})]}),i.jsx(We,{position:[0,2.2,0],text:P,tone:r?"ok":o?"critical":"accent",ctx:n,keep:s})]})}const ft=1.15,_s=n=>n.startsWith("agent:")?n.slice(6):"";function Jt(n,t,s){const e=n*Math.PI/3+t*.28;return s.set(Oe[0]+ft*Math.cos(e),Oe[1]+.12*Math.sin(e*2+n),Oe[2]+ft*Math.sin(e))}function Os({ctx:n,nodes:t,packet:s,fx:e}){const r=f.useRef([]),o=f.useRef([]),u=f.useRef([]),c=f.useRef(dt.map(()=>1)),l=f.useRef(null),p=f.useRef(null),h=f.useRef({nodes:t,packet:s});h.current={nodes:t,packet:s};const[d,m,y]=f.useMemo(()=>[new j,new j,new j],[]),P=f.useMemo(()=>new j(...vn),[]),T=Dt(n.palette,(s==null?void 0:s.tone)??e.tone),L=(S,w,v)=>{const M=_s(S);if(M){const O=dt.indexOf(M);if(O>=0)return Jt(O,w,v),!0}return S==="human"?(v.copy(P),!0):!1};return U((S,w)=>{const{nodes:v,packet:M}=h.current,O=n.reduced?0:n.time.current,E=n.alpha.current,te=1-Math.exp(-w*6);dt.forEach((A,J)=>{var ee;const Y=r.current[J];if(!Y)return;Jt(J,O,Y.position);const de=`agent:${A}`,I=((ee=v[de])==null?void 0:ee.phase)==="active"||(M==null?void 0:M.from)===de||(M==null?void 0:M.to)===de;c.current[J]+=((I?1.7:1)-c.current[J])*te,Y.scale.setScalar(c.current[J]);const ye=Y.children[0];ye.material.opacity=(I?1:.55)*E;const z=o.current[J];z&&(z.material.opacity=(I?.45+(n.reduced?0:.2*Math.sin(n.time.current*5)):.12)*E,z.lookAt(S.camera.position));const Z=u.current[J];Z&&(Z.style.opacity=String(I?E:0))});const B=l.current,C=p.current,_=!!M&&!n.reduced&&L(M.from,O,d)&&L(M.to,O,m);if(B&&(B.visible=_,_&&(y.copy(d).add(m).multiplyScalar(.5),y.y+=.9,B.setPoints(d,m,y),B.material.opacity=.85*E)),C&&(C.visible=_,_)){const A=et(ge(n.pktAge.current/.6));C.position.set((1-A)*(1-A)*d.x+2*(1-A)*A*y.x+A*A*m.x,(1-A)*(1-A)*d.y+2*(1-A)*A*y.y+A*A*m.y,(1-A)*(1-A)*d.z+2*(1-A)*A*y.z+A*A*m.z),C.material.opacity=E}}),i.jsxs("group",{children:[i.jsxs("mesh",{position:Oe,"rotation-x":-Math.PI/2,children:[i.jsx("ringGeometry",{args:[ft-.01,ft+.01,64]}),i.jsx("meshBasicMaterial",{...N(n.palette.border,.5)})]}),dt.map((S,w)=>i.jsxs("group",{ref:v=>{r.current[w]=v},children:[i.jsxs("mesh",{children:[i.jsx("sphereGeometry",{args:[.1,20,14]}),i.jsx("meshBasicMaterial",{...N(At[S],.55)})]}),i.jsxs("mesh",{ref:v=>{o.current[w]=v},children:[i.jsx("ringGeometry",{args:[.15,.2,28]}),i.jsx("meshBasicMaterial",{...N(At[S],.12),side:Te})]}),i.jsx(Re,{position:[0,.3,0],center:!0,zIndexRange:[25,0],style:{pointerEvents:"none"},children:i.jsx("span",{ref:v=>{u.current[w]=v},className:"scn-holo scn-holo--mini",style:{opacity:0,borderColor:At[S]},children:vs[S]})})]},S)),i.jsx(ps,{ref:l,start:[0,0,0],end:[1,0,0],mid:[.5,1,0],color:T,lineWidth:2.4,transparent:!0,visible:!1}),i.jsxs("mesh",{ref:p,visible:!1,children:[i.jsx("sphereGeometry",{args:[.07,14,10]}),i.jsx("meshBasicMaterial",{...N(T,1)})]})]})}function Ts({fx:n,ctx:t}){const s=Ue(n.site)??[0,0,0],e=Dt(t.palette,n.tone==="ok"?"accent":n.tone),r=f.useRef(null),o=f.useRef(null),u=f.useRef(null);U(()=>{const l=t.alpha.current;if(r.current){const p=t.reduced?.5:t.age.current%1.5/1.5;r.current.position.y=.05+1.5*p,r.current.material.opacity=.9*Math.sin(Math.PI*p)*l}o.current&&(o.current.material.opacity=.12*l),u.current&&(u.current.scale.setScalar(t.reduced?1:1+.15*Math.sin(t.time.current*6)),u.current.material.opacity=.55*l)});const c=n.label??"";return i.jsxs("group",{position:s,children:[i.jsxs("mesh",{ref:r,"rotation-x":-Math.PI/2,children:[i.jsx("ringGeometry",{args:[.52,.62,48]}),i.jsx("meshBasicMaterial",{...N(e,0),side:Te})]}),i.jsxs("mesh",{ref:o,"position-y":.85,children:[i.jsx("cylinderGeometry",{args:[.15,.65,1.7,32,1,!0]}),i.jsx("meshBasicMaterial",{...N(e,.12),side:Te})]}),i.jsxs("mesh",{ref:u,"position-y":1.75,children:[i.jsx("octahedronGeometry",{args:[.1]}),i.jsx("meshBasicMaterial",{...N(e,.55)})]}),c&&i.jsx(We,{position:[0,2.15,0],text:c,tone:n.tone,ctx:t})]})}const Ae=(n,t,s)=>[n[0]+t,0,n[2]+s],qe={"gap:GAP-IN-01":Ae(ue,.9,-.5),"gap:GAP-IN-02":Ae(F["GW-IN-2"].pos,.8,.7),"gap:GAP-IN-03":Ae(V["CHN-01"].pos,-.9,-.3),"gap:GAP-IN-04":Ae(V["CHN-04"].pos,-.8,.6),"gap:GAP-IN-05":Ae(ue,-.4,.9),"gap:GAP-IN-06":Ae(F["GW-IN-1"].pos,.8,.8),"gap:GAP-IN-07":[.1,0,-.6],"gap:GAP-IN-08":Ae(F["GW-IN-2"].pos,1.4,-.5),"gap:GAP-IN-09":[-1.6,0,-2.6]};function Ls({id:n,ctx:t}){const s=f.useRef(null),e=f.useRef(null),r=qe[n];return U(()=>{if(!s.current)return;e.current??(e.current=t.time.current);const o=t.time.current-e.current,u=t.reduced?1:et(o/.65),c=t.reduced||o<.65?0:Math.exp(-(o-.65)*5)*Math.sin((o-.65)*18)*.12;s.current.position.set(r[0],(1-u)*2.6+c,r[2])}),i.jsxs("group",{ref:s,position:[r[0],2.6,r[2]],children:[i.jsxs("mesh",{"position-y":.02,"rotation-x":-Math.PI/2,children:[i.jsx("circleGeometry",{args:[.1,20]}),i.jsx("meshBasicMaterial",{...N(Pt,.5)})]}),i.jsxs("mesh",{"position-y":.4,children:[i.jsx("cylinderGeometry",{args:[.014,.014,.8,6]}),i.jsx("meshBasicMaterial",{...N(Pt,1)})]}),i.jsxs("mesh",{position:[.17,.7,0],children:[i.jsx("planeGeometry",{args:[.34,.22]}),i.jsx("meshBasicMaterial",{...N(Pt,.95),side:Te})]})]})}function Rs({ctx:n,nodes:t,fx:s}){const e=f.useMemo(()=>Object.keys(qe).filter(o=>{var u,c,l;return(((u=t[o])==null?void 0:u.phase)==="active"||((c=t[o])==null?void 0:c.phase)==="done")&&((l=t[o])==null?void 0:l.at)}),[t]),r=s.kind==="gap"&&qe[s.node]&&e.includes(s.node)?s.node:null;return i.jsxs("group",{children:[e.map(o=>i.jsx(Ls,{id:o,ctx:n},o)),r&&s.label&&i.jsx(We,{position:[qe[r][0],1.45,qe[r][2]],text:s.label,tone:"gap",ctx:n})]})}const Cs=new Set(on.filter(n=>n.kind==="threat"&&n.group==="attack").map(n=>n.id)),en=1.7;function Mn({pos:n,color:t,ctx:s,startAt:e=0,ripples:r=2}){const o=f.useRef([]),u=f.useRef(null);return U(()=>{const c=s.age.current-e;for(let l=0;l<r;l++){const p=o.current[l];if(!p)continue;const h=p.material;if(s.reduced){p.scale.setScalar(2+l*.6),h.opacity=c>0?.55-l*.2:0;continue}const d=c>0?(c-l*.55)%1.6/1.6:-1;if(d<0||c<l*.55){h.opacity=0;continue}p.scale.setScalar(.05+3*et(d)),h.opacity=(1-d)*.85*s.alpha.current}if(u.current){const l=u.current.material;l.opacity=(c>0?.22+(s.reduced?0:.12*Math.sin(s.time.current*6)):0)*s.alpha.current}}),i.jsxs("group",{position:[n[0],.03,n[2]],"rotation-x":-Math.PI/2,children:[i.jsxs("mesh",{ref:u,children:[i.jsx("circleGeometry",{args:[.7,40]}),i.jsx("meshBasicMaterial",{...N(t,0)})]}),Array.from({length:r},(c,l)=>i.jsxs("mesh",{ref:p=>{o.current[l]=p},children:[i.jsx("ringGeometry",{args:[.9,1,56]}),i.jsx("meshBasicMaterial",{...N(t,0),side:Te})]},l))]})}function Ds({fx:n,ctx:t}){const s=n.node.startsWith("threat:")?n.node.slice(7):"",e=n.site??"CHN-01",r=Ue(e)??Ue("CHN-01"),o=Cs.has(n.node),u=t.truth&&o&&!t.reduced,c=t.palette.critical,l=f.useMemo(()=>{const m=yn(s,e),y=[m[0],2.2,m[2]],P=[r[0],.95,r[2]],T=[ue[0],.9,ue[2]],L=[le[0],le[1]-.5,le[2]],S=e==="SAT-MGMT"?[y,T]:gn(s)?[y,T,P]:[y,L,P];return jn(S,.55)},[s,e,r[0],r[2]]),p=f.useRef(0);U(()=>{p.current=ge(t.age.current/en)});const h=u?en:0,d=f.useRef(null);return U(()=>{if(!d.current)return;const m=t.reduced?1:1+.25*Math.sin(t.time.current*7);d.current.scale.setScalar(m),d.current.material.opacity=(t.age.current>h?.5:.15)*t.alpha.current}),i.jsxs("group",{children:[u&&i.jsx(pt,{curve:l,color:c,radius:.04,dash:16,speed:3,progress:p,ctx:t}),i.jsx(Mn,{pos:r,color:c,ctx:t,startAt:h}),i.jsxs("mesh",{ref:d,position:[r[0],.95,r[2]],children:[i.jsx("sphereGeometry",{args:[.22,20,14]}),i.jsx("meshBasicMaterial",{...N(c,.4)})]}),n.label&&i.jsx(We,{position:[r[0],2.05,r[2]],text:n.label,tone:"critical",ctx:t})]})}function Ns({pos:n,final:t,ctx:s}){const e=f.useRef(null),r=f.useMemo(()=>new je(s.palette.accent),[s.palette.accent]),o=f.useMemo(()=>new je(t),[t]),u=f.useMemo(()=>new je,[]);return U(()=>{if(!e.current)return;const c=s.age.current,l=s.reduced?1:et((c-1)/.6);u.copy(r).lerp(o,l);const p=s.reduced?1:et(c/.6);e.current.scale.set(1,p,1),e.current.position.y=s.reduced?0:(1-p)*-.2,e.current.traverse(h=>{var m;const d=h.material;d&&d.type==="MeshBasicMaterial"&&(d.color.copy(u),d.opacity=((m=d.userData).o??(m.o=d.opacity))*s.alpha.current*(s.reduced?1:.85+.15*Math.sin(s.time.current*4)))})}),i.jsx("group",{position:[n[0]-.95,0,n[2]+.5],children:i.jsxs("group",{ref:e,children:[i.jsxs("mesh",{"position-y":.47,children:[i.jsx("cylinderGeometry",{args:[.04,.09,.95,8]}),i.jsx("meshBasicMaterial",{...N("#fff",.9,{wireframe:!0})})]}),i.jsxs("mesh",{"position-y":.97,children:[i.jsx("sphereGeometry",{args:[.1,10,8]}),i.jsx("meshBasicMaterial",{...N("#fff",.9,{wireframe:!0})})]}),i.jsxs("mesh",{position:[.4,.12,.2],children:[i.jsx("boxGeometry",{args:[.3,.24,.24]}),i.jsx("meshBasicMaterial",{...N("#fff",.9,{wireframe:!0})})]}),i.jsxs("mesh",{"position-y":.01,"rotation-x":-Math.PI/2,children:[i.jsx("ringGeometry",{args:[.32,.4,32]}),i.jsx("meshBasicMaterial",{...N("#fff",.7)})]})]})})}const Is=n=>{const t=V[n].pos;return new un(new j(t[0],.95,t[2]),new j(...le))};function Bs({pct:n,first:t,color:s,ctx:e}){const r=f.useMemo(()=>[t,...Object.keys(V).filter(c=>c!==t)].filter(c=>V[c]),[t]),o=f.useMemo(()=>r.map(Is),[r]),u=Math.max(1,Math.ceil(n/100*r.length));return i.jsx("group",{children:o.map((c,l)=>i.jsx(pt,{curve:c,color:s,radius:.05,dash:8,speed:1.5,solid:.65,progress:()=>l<u?ge((e.age.current-l*.08)/.9):0,ctx:e},r[l]))})}function zs({site:n,gw:t,color:s,blocked:e,ctx:r}){var l;const o=((l=V[n])==null?void 0:l.pos)??V["CHN-01"].pos,u=(F[t]??F["GW-IN-2"]).pos,c=f.useMemo(()=>jn([[o[0],.95,o[2]],[u[0],.9,u[2]]],.9),[o[0],o[2],u[0],u[2]]);return i.jsx(pt,{curve:c,color:s,radius:.055,dash:9,speed:3.5,solid:.15,progress:()=>Math.min(e?.55:1,ge(r.age.current/1.3)),ctx:r})}function Gs({pos:n,blocked:t,ctx:s}){const e=f.useRef(null),r=f.useRef(null),o=f.useRef(1),u=f.useMemo(()=>[n[0]+2.2,2.6,n[2]-1.9],[n]),c=new j(n[0],.65,n[2]),l=f.useMemo(()=>{const m=new j(...u).sub(c).normalize().multiplyScalar(.8);return c.clone().add(m)},[u,n]),p=f.useMemo(()=>new un(new j(...u),t?l:new j(n[0],.95,n[2])),[u,l,t,n]),h=t?s.palette.accent:s.palette.critical,d=f.useRef(0);return U(()=>{const m=s.age.current;d.current=ge(m/.5),o.current=s.reduced?1:1-ge((m-.55)/.35);const y=s.reduced?.5:Math.max(0,1-(m-.5)/.7)*(m>.5?1:0),P=s.reduced?1:1+.3*ge((m-.9)/.9),T=s.alpha.current*(s.reduced?1:1-.7*ge((m-1)/1.2));for(const L of[e.current,r.current])L&&L.scale.setScalar(P);e.current&&(e.current.material.opacity=(.1+.45*y)*T),r.current&&(r.current.material.opacity=(.5+.5*y)*T)}),i.jsxs("group",{children:[!s.reduced&&i.jsx(pt,{curve:p,color:s.palette.critical,radius:.04,dash:10,speed:5,solid:.6,progress:d,alpha:o,ctx:s}),i.jsxs("group",{position:[n[0],.65,n[2]],children:[i.jsxs("mesh",{ref:e,children:[i.jsx("sphereGeometry",{args:[.78,24,16]}),i.jsx("meshBasicMaterial",{...N(h,.1)})]}),i.jsxs("mesh",{ref:r,children:[i.jsx("icosahedronGeometry",{args:[.8,2]}),i.jsx("meshBasicMaterial",{...N(h,.5,{wireframe:!0})})]})]})]})}function Us({fx:n,ctx:t,nodes:s}){const e=n.node.startsWith("exec:")?n.node.slice(5):"",r=(n.site&&V[n.site]?n.site:Ms(s))??"CHN-01",o=Ue(r)??V["CHN-01"].pos,u=t.palette.ok,c=t.palette.critical,l=s[n.node],p=(l==null?void 0:l.tone)==="critical",h=wn(s);let d=null;if(e==="clone"||e==="rollback"){const m=e==="rollback"||p?c:u;d=i.jsx(Ns,{pos:o,final:m,ctx:t})}else e==="r5"||e==="r25"||e==="r100"?d=i.jsx(Bs,{pct:e==="r5"?5:e==="r25"?25:100,first:r,color:p?c:u,ctx:t}):e==="cleanpath"||e==="failover"?d=i.jsx(zs,{site:r,gw:h,color:p||h==="GW-XX"?c:u,blocked:p||h==="GW-XX",ctx:t}):e==="reattack"?d=i.jsx(Gs,{pos:o,blocked:(l==null?void 0:l.word)==="BLOCKED",ctx:t}):e==="return"&&(d=i.jsx(Mn,{pos:o,color:u,ctx:t,ripples:1}));return i.jsxs("group",{children:[d,n.label&&i.jsx(We,{position:[o[0],2.05,o[2]],text:n.label,tone:p?"critical":"ok",ctx:t})]})}const tn=64,nn=6;function ks({fx:n,ctx:t}){const s=Dt(t.palette,n.tone==="ok"||n.tone==="accent"?"warn":n.tone),e=f.useRef(null),r=f.useRef(null),o=f.useRef(null),u=f.useRef(null),c=f.useMemo(()=>new Hn(.78,.86,tn),[]);U((d,m)=>{const y=t.alpha.current;e.current&&!t.reduced&&(e.current.rotation.y+=m*.9,e.current.position.y=Math.sin(t.time.current*1.6)*.06);const P=t.reduced?0:Math.max(0,1-t.age.current*1.4);r.current&&(r.current.material.opacity=(.22+.5*P)*y),o.current&&(o.current.material.opacity=.9*y);const T=t.reduced?.6:1-ge(t.age.current%(nn+1)/nn);c.setDrawRange(0,Math.max(0,Math.round(tn*T))*6),u.current&&(u.current.material.opacity=.85*y)});const[l,p,h]=Ke;return i.jsxs("group",{position:[l,p,h],children:[i.jsxs("group",{ref:e,children:[i.jsxs("mesh",{ref:r,scale:[.6,.85,.6],children:[i.jsx("octahedronGeometry",{args:[.5]}),i.jsx("meshBasicMaterial",{...N(s,.25)})]}),i.jsxs("mesh",{ref:o,scale:[.6,.85,.6],children:[i.jsx("octahedronGeometry",{args:[.52]}),i.jsx("meshBasicMaterial",{...N(s,.9,{wireframe:!0})})]})]}),i.jsx("mesh",{ref:u,geometry:c,"rotation-x":-Math.PI/2,"position-y":-.1,children:i.jsx("meshBasicMaterial",{...N(s,.85),side:Te})}),n.label&&i.jsx(We,{position:[0,.95,0],text:n.label,tone:n.tone==="ok"?"ok":"warn",ctx:t})]})}const sn=3.5,Ws=.8,Hs=(n,t)=>n.kind===t.kind&&n.site===t.site&&n.node===t.node&&n.label===t.label&&n.tone===t.tone;function Fs(){const[n,t]=f.useState(xn);return f.useEffect(()=>{const s=()=>{const e=we.getState(),r=js(e.beats[e.beats.length-1],e.current,e.nodes,e.anomalySite);t(o=>Hs(o,r)?o:r)};return s(),we.subscribe(s)},[]),n}function Vs({fx:n,palette:t,truth:s,reduced:e}){const r=we(d=>d.nodes),o=we(d=>d.current),u=we(d=>d.pending.length>0),c=we(d=>d.beats.length?d.beats[d.beats.length-1].id:0),l=(o==null?void 0:o.id)??0,p=f.useRef({palette:t,reduced:e,truth:s,age:{current:0},pktAge:{current:99},alpha:{current:1},time:{current:0}}).current;p.palette=t,p.reduced=e,p.truth=s;const h=f.useRef(0);return f.useEffect(()=>{p.age.current=0},[p,n.kind,n.site,n.node,c]),f.useEffect(()=>{h.current=0},[c,l]),f.useEffect(()=>{p.pktAge.current=0},[p,l]),U((d,m)=>{const y=Math.min(m,.1);p.time.current+=y,p.age.current+=y,p.pktAge.current+=y,h.current+=y,p.alpha.current=h.current<sn?1:Math.max(0,1-(h.current-sn)/Ws)}),i.jsxs("group",{children:[n.kind==="threat"&&i.jsx(Ds,{fx:n,ctx:p}),n.kind==="detect"&&i.jsx(Ts,{fx:n,ctx:p}),n.kind==="coordinate"&&i.jsx(Os,{fx:n,ctx:p,nodes:r,packet:o}),n.kind==="rules"&&i.jsx(ks,{fx:n,ctx:p}),(n.kind==="commander"||u)&&i.jsx(As,{ctx:p,nodes:r,pending:u}),n.kind==="heal"&&i.jsx(Us,{fx:n,ctx:p,nodes:r}),i.jsx(Rs,{ctx:p,nodes:r,fx:n})]})}const rn=()=>{const n=getComputedStyle(document.documentElement),t=(s,e)=>n.getPropertyValue(s).trim()||e;return{bg:t("--bg","#111316"),surface:t("--surface","#1A1D21"),surface2:t("--surface-2","#22262B"),ink:t("--ink","#E7E9EC"),muted:t("--ink-muted","#9AA3AE"),border:t("--border","#2A2E34"),accent:t("--accent","#7FA7CF"),ok:t("--ok","#74B08C"),warn:t("--warn","#D6A24E"),critical:t("--critical","#E07F72"),healing:t("--healing","#A39BDA"),unknown:t("--unknown","#8A8F98")}},En=(n,t)=>t==="down"?n.critical:t==="degraded"?n.warn:t==="healing"?n.healing:t==="ok"?n.ok:n.unknown;function ht({name:n,palette:t,scale:s=1,opacity:e=1,...r}){const{scene:o}=dn("./models/orca-assets.glb"),u=f.useMemo(()=>{const c=o.getObjectByName(n);if(!c)return null;const l=c.clone(!0);return l.position.set(0,0,0),l.traverse(p=>{const h=p;if(!h.isMesh)return;const m=h.material.name,y=m==="panel"?t.accent:m==="accent"?t.warn:m==="dark"?t.surface:t.muted;h.material=new $n({color:y,roughness:.85,metalness:0,transparent:e<1,opacity:e})}),l},[o,n,t,e]);return u?i.jsx("group",{...r,scale:s,children:i.jsx("primitive",{object:u})}):null}function $s({palette:n}){const t=f.useMemo(()=>[[2.2,.01,-4.5],[2,.01,-3],[2.3,.01,-1.4],[2.1,.01,.2],[2.4,.01,1.6],[2.3,.01,3.2],[2.6,.01,4.5]],[]);return i.jsxs("group",{children:[i.jsxs("mesh",{"rotation-x":-Math.PI/2,position:[-1.5,-.01,0],children:[i.jsx("planeGeometry",{args:[9,10]}),i.jsx("meshStandardMaterial",{color:n.surface,roughness:1})]}),i.jsxs("mesh",{"rotation-x":-Math.PI/2,position:[5,-.02,0],children:[i.jsx("planeGeometry",{args:[5,10]}),i.jsx("meshStandardMaterial",{color:n.bg,roughness:1})]}),i.jsx("gridHelper",{args:[14,28,n.border,n.border],position:[0,.001,0]}),i.jsx(Me,{points:t,color:n.accent,lineWidth:1.2,transparent:!0,opacity:.55})]})}function Ys({palette:n}){const t=f.useRef(null),s=mt();U(({clock:r})=>{t.current&&!s&&(t.current.rotation.y=Math.sin(r.elapsedTime*.15)*.25)});const e=f.useMemo(()=>new Vn(0,0,9,9,Math.PI*.15,Math.PI*.85).getPoints(48).map(r=>[r.x-.6,5.2+(r.y-9*Math.sin(Math.PI/2))*.25,-.4]),[]);return i.jsxs("group",{children:[i.jsx(Me,{points:e,color:n.border,lineWidth:1,dashed:!0,dashSize:.2,gapSize:.15}),i.jsx("group",{ref:t,position:le,children:i.jsx(ht,{name:"Satellite",palette:n,scale:1.3})}),i.jsx(Re,{position:[le[0],le[1]+.9,le[2]],center:!0,children:i.jsx("span",{className:"scn-label scn-label--sat",children:"GEO satellite · emulated"})})]})}function Xs({palette:n,sites:t,paths:s}){return i.jsxs("group",{children:[Object.entries(V).map(([e,r])=>{const o=t[e],u=s.find(m=>m.site===e&&m.active),c=(u==null?void 0:u.gateway)??(o==null?void 0:o.gateway)??"GW-IN-1",l=F[c]??F["GW-IN-1"],p=En(n,o==null?void 0:o.state),h=!(u!=null&&u.path)||u.path==="A"||c.startsWith("GW"),d=[r.pos[0],.95,r.pos[2]];return i.jsxs("group",{children:[h?i.jsx(Me,{points:[d,le],color:p,lineWidth:(o==null?void 0:o.state)==="down"?1:1.6,transparent:!0,opacity:(o==null?void 0:o.state)==="down"?.35:.85,dashed:(o==null?void 0:o.state)==="down",dashSize:.18,gapSize:.14}):null,u&&u.path!=="A"&&i.jsx(Me,{points:[d,[(d[0]+l.pos[0])/2,1.6,(d[2]+l.pos[2])/2],[l.pos[0],.9,l.pos[2]]],color:n.healing,lineWidth:2})]},e)}),Object.entries(F).filter(([,e])=>!e.foreign).map(([e,r])=>i.jsx(Me,{points:[[r.pos[0],1,r.pos[2]],le],color:n.accent,lineWidth:1,transparent:!0,opacity:.45},e))]})}function Zs({palette:n,sites:t,focus:s}){return i.jsx("group",{children:Object.entries(V).map(([e,r])=>{const o=t[e],u=En(n,o==null?void 0:o.state);return i.jsxs("group",{position:r.pos,children:[i.jsxs("mesh",{"rotation-x":-Math.PI/2,"position-y":.005,children:[i.jsx("ringGeometry",{args:[.32,.4,40]}),i.jsx("meshBasicMaterial",{color:u,transparent:!0,opacity:.9})]}),i.jsx(ht,{name:"CellTower",palette:n,scale:.95}),i.jsx(ht,{name:"UserTerminal",palette:n,scale:.32,position:[.45,0,.25]}),i.jsx(Re,{position:[0,1.25,0],center:!0,children:i.jsxs("span",{className:`scn-label ${s===e?"is-focus":""}`,"data-state":(o==null?void 0:o.state)??"unknown",children:[i.jsx("span",{className:"scn-dot"}),r.name,o!=null&&o.state&&o.state!=="ok"?i.jsx("b",{children:o.state.toUpperCase()}):null]})})]},e)})})}function Ks({palette:n,gateways:t}){return i.jsx("group",{children:Object.entries(F).map(([s,e])=>i.jsxs("group",{position:e.pos,children:[i.jsx(ht,{name:"GatewayDish",palette:n,scale:1.1,opacity:e.foreign?.35:1}),i.jsx(Re,{position:[0,1.4,0],center:!0,children:i.jsxs("span",{className:"scn-label","data-state":e.foreign?"locked":t[s]==="down"?"down":"ok",children:[i.jsx("span",{className:"scn-dot"}),e.name,i.jsx("b",{children:e.foreign?"NOT ALLOWED":(t[s]??"up").toUpperCase()})]})})]},s))})}function qs({palette:n,target:t,injector:s}){const e=f.useRef(null),r=f.useRef(null),o=f.useRef(null),u=mt();if(f.useEffect(()=>{o.current=null},[t,s]),U(({clock:l})=>{e.current&&!u&&(e.current.rotation.y=l.elapsedTime,e.current.position.y=2.2+Math.sin(l.elapsedTime*2)*.08),r.current&&(o.current??(o.current=l.elapsedTime),r.current.scale.setScalar(u?1:Math.min(1,(l.elapsedTime-o.current)/.6)))}),!t)return null;const c=yn(s,t);return i.jsxs("group",{ref:r,position:c,children:[i.jsxs("mesh",{ref:e,"position-y":2.2,children:[i.jsx("octahedronGeometry",{args:[.22]}),i.jsx("meshStandardMaterial",{color:n.critical,roughness:.6})]}),i.jsx(Me,{points:[[0,2.2,0],[0,.05,0]],color:n.critical,lineWidth:1.2,dashed:!0,dashSize:.12,gapSize:.1}),i.jsx(Re,{position:[0,2.85,0],center:!0,children:i.jsx("span",{className:"scn-label scn-label--threat",children:"Threat source · director view"})})]})}function Qs({palette:n}){const t=F["GW-IN-1"].pos;return i.jsxs("group",{children:[i.jsxs("group",{position:ue,children:[i.jsxs("mesh",{"position-y":.3,children:[i.jsx("boxGeometry",{args:[.6,.6,.42]}),i.jsx("meshStandardMaterial",{color:n.surface2,roughness:.9})]}),i.jsxs("mesh",{"position-y":.62,children:[i.jsx("boxGeometry",{args:[.6,.05,.42]}),i.jsx("meshStandardMaterial",{color:n.accent,roughness:.8})]}),i.jsx(Re,{position:[0,.95,0],center:!0,children:i.jsxs("span",{className:"scn-label scn-label--mgmt",children:[i.jsx("span",{className:"scn-dot"}),"SAT-MGMT"]})})]}),i.jsx(Me,{points:[[ue[0],.6,ue[2]],[t[0],.9,t[2]]],color:n.border,lineWidth:1,dashed:!0,dashSize:.12,gapSize:.1})]})}function Js({focus:n,fx:t}){const{camera:s}=Q(),e=Q(d=>d.controls),r=f.useRef(new j(0,1.2,0)),o=f.useRef(new j(0,1.2,0)),u=f.useRef(new j(...Qt)),c=f.useRef(0),l=mt(),p=f.useRef(we.getState().nodes);f.useEffect(()=>we.subscribe(d=>{p.current=d.nodes}),[]),f.useEffect(()=>{var y,P;const d=Es(t,p.current);if(d){o.current.set(...d.target),u.current.set(...d.offset);return}const m=n?((y=V[n])==null?void 0:y.pos)??((P=F[n])==null?void 0:P.pos):null;o.current.set(m?m[0]*.5:0,1.2,m?m[2]*.5:0),u.current.set(...Qt)},[n,t]),f.useEffect(()=>{if(!e)return;const d=()=>{c.current=performance.now()+8e3};return e.addEventListener("start",d),e.addEventListener("end",d),()=>{e.removeEventListener("start",d),e.removeEventListener("end",d)}},[e]);const h=f.useMemo(()=>new j,[]);return U((d,m)=>{if(performance.now()<c.current){e==null||e.update();return}const y=l?1:1-Math.exp(-Math.min(m,.1)*3.2);r.current.lerp(o.current,y),h.copy(r.current).add(u.current),s.position.lerp(h,y),e?(e.target.copy(r.current),e.update()):s.lookAt(r.current)}),null}function mt(){const[n,t]=f.useState(()=>window.matchMedia("(prefers-reduced-motion: reduce)").matches);return f.useEffect(()=>{const s=window.matchMedia("(prefers-reduced-motion: reduce)"),e=()=>t(s.matches);return s.addEventListener("change",e),()=>s.removeEventListener("change",e)},[]),n}function rr({truth:n}){const t=Tn(w=>w.theme),[s,e]=f.useState(rn);f.useEffect(()=>{const w=requestAnimationFrame(()=>e(rn()));return()=>cancelAnimationFrame(w)},[t]);const r=it(w=>w.sites),o=it(w=>w.gateways),u=it(w=>w.paths),c=it(w=>w.truth),[l,p]=f.useState(null),h=f.useRef({});f.useEffect(()=>{for(const[w,v]of Object.entries(r))h.current[w]&&h.current[w]!==v.state&&p(v.state==="ok"?null:w),h.current[w]=v.state},[r]);const d=n?c.filter(w=>w.kind==="inject").slice(-1)[0]:void 0,m=d?String(d.target??""):null,y=m&&(V[m]||F[m])?m:m?"CHN-01":null,P=d&&String(d.truth_class??"").startsWith("attack"),T=d?String(d.injector??""):"",L=Fs(),S=mt();return i.jsxs("div",{className:"scn","data-theme-key":t,children:[i.jsxs(Fn,{dpr:[1,2],camera:{position:[7.5,7.2,6.5],fov:38},gl:{antialias:!0,powerPreference:"high-performance"},children:[i.jsx("color",{attach:"background",args:[s.bg]}),i.jsx("fog",{attach:"fog",args:[s.bg,16,30]}),i.jsx("hemisphereLight",{args:[s.ink,s.bg,.9]}),i.jsx("directionalLight",{position:[4,8,3],intensity:1.1}),i.jsxs(f.Suspense,{fallback:null,children:[i.jsx($s,{palette:s}),i.jsx(Xs,{palette:s,sites:r,paths:u}),i.jsx(Zs,{palette:s,sites:r,focus:l}),i.jsx(Ks,{palette:s,gateways:o}),i.jsx(Ys,{palette:s}),n&&P&&i.jsx(qs,{palette:s,target:y,injector:T}),i.jsx(Qs,{palette:s}),i.jsx(Vs,{fx:L,palette:s,truth:n,reduced:S})]}),i.jsx(ms,{makeDefault:!0,enablePan:!1,enableZoom:!1,enableDamping:!0,dampingFactor:.12,maxPolarAngle:Math.PI/2.15,minPolarAngle:.35}),i.jsx(Js,{focus:l,fx:L})]}),i.jsx("div",{className:"scn-tag mono",children:"EMULATED NETWORK · CHENNAI"}),i.jsxs("div",{className:"scn-legend",children:[i.jsxs("span",{"data-state":"ok",children:[i.jsx("i",{}),"OK"]}),i.jsxs("span",{"data-state":"degraded",children:[i.jsx("i",{}),"Degraded"]}),i.jsxs("span",{"data-state":"down",children:[i.jsx("i",{}),"Down"]}),i.jsxs("span",{"data-state":"healing",children:[i.jsx("i",{}),"Healing"]})]})]})}dn.preload("./models/orca-assets.glb");export{rr as NetworkScene};
