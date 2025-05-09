import re
import warnings
from io import open  # Consistent binary I/O from Python 2 and 3
import numpy as np
import pegasus_read as pegr
from matplotlib import pyplot as plt
from scipy.interpolate import spline

betai0 = 0.11111 #1.0 
tcorr = 24.0 #40.0
asp = 6.0 #8.0
tcross = tcorr*2.0*3.1415926536

t0turb = 850.0
t1turb = 1000.0 #1141.0

id_particle = [0,1] 
n_procs = 500 #384*64
id_proc = np.arange(n_procs)
Nparticle = np.float(len(id_particle))*np.float(len(id_proc))
path_read = "../track/"
path_save = "../figures/"
prob = "turb"
fig_frmt = ".png"

for ii in range(len(id_proc)):
  for jj in range(len(id_particle)):
    data = pegr.tracked_read(path_read,prob,id_particle[jj],id_proc[ii])

  #tracked particle files keywords
  # [1]=time     [2]=x1       [3]=x2       [4]=x3       [5]=v1       [6]=v2       [7]=v3       [8]=B1       [9]=B2       [10]=B3       [11]=E1       [12]=E2       [13]=E3       [14]=U1       [15]=U2       [16]=U3       [17]=dens     [18]=F1       [19]=F2       [20]=F3


    t_ = data[u'time']
    #x1_ = data[u'x1']
    #x2_ = data[u'x2']
    #x3_ = data[u'x3']
    v1_ = data[u'v1']
    v2_ = data[u'v2']
    v3_ = data[u'v3']
    B1_ = data[u'B1']
    B2_ = data[u'B2']
    B3_ = data[u'B3']
    E1_ = data[u'E1']
    E2_ = data[u'E2']
    E3_ = data[u'E3']
    #U1_ = data[u'U1']
    #U2_ = data[u'U2']
    #U3_ = data[u'U3']
    #Dn_ = data[u'dens']
    #F1_ = data[u'F1']
    #F2_ = data[u'F2']
    #F3_ = data[u'F3']

    Bmod = np.sqrt(B1_*B1_ + B2_*B2_ + B3_*B3_)
    v_para = ( v1_*B1_ + v2_*B2_ + v3_*B3_) / Bmod
    E_para = ( E1_*B1_ + E2_*B2_ + E3_*B3_) /  Bmod
    #
    v_perp1 = v1_ - v_para*B1_/Bmod
    v_perp2 = v2_ - v_para*B2_/Bmod
    v_perp3 = v3_ - v_para*B3_/Bmod
    #
    E_perp1 = E1_ - E_para*B1_/Bmod
    E_perp2 = E2_ - E_para*B2_/Bmod
    E_perp3 = E3_ - E_para*B3_/Bmod
    #
    Qtot_ = v1_*E1_ + v2_*E2_ + v3_*E3_
    Qpar_ = v_para*E_para
    Qprp_ = v_perp1*E_perp1 + v_perp2*E_perp2 + v_perp3*E_perp3
  
    if ( (ii == 0) and (jj == 0)):
      #creating regular time axis
      t0 = t_[0]
      t1 = t_[len(t_)-1]
      nt = len(t_)
      t_real, dt = np.linspace(t0,t1,nt,retstep=True)

    #regularize time series on uniformly distributed time grid
    print "\n [ regularizing time series ]"
    #x1 = np.array([np.interp(t_real[i], t_, x1_) for i in  range(nt)])
    #x2 = np.array([np.interp(t_real[i], t_, x2_) for i in  range(nt)])
    #x3 = np.array([np.interp(t_real[i], t_, x3_) for i in  range(nt)])
    #v1 = np.array([np.interp(t_real[i], t_, v1_) for i in  range(nt)])
    #v2 = np.array([np.interp(t_real[i], t_, v2_) for i in  range(nt)])
    #v3 = np.array([np.interp(t_real[i], t_, v3_) for i in  range(nt)])
    #B1 = np.array([np.interp(t_real[i], t_, B1_) for i in  range(nt)])
    #B2 = np.array([np.interp(t_real[i], t_, B2_) for i in  range(nt)])
    #B3 = np.array([np.interp(t_real[i], t_, B3_) for i in  range(nt)])
    #E1 = np.array([np.interp(t_real[i], t_, E1_) for i in  range(nt)])
    #E2 = np.array([np.interp(t_real[i], t_, E2_) for i in  range(nt)])
    #E3 = np.array([np.interp(t_real[i], t_, E3_) for i in  range(nt)])
    #U1 = np.array([np.interp(t_real[i], t_, U1_) for i in  range(nt)])
    #U2 = np.array([np.interp(t_real[i], t_, U2_) for i in  range(nt)])
    #U3 = np.array([np.interp(t_real[i], t_, U3_) for i in  range(nt)])
    #Dn = np.array([np.interp(t_real[i], t_, Dn_) for i in  range(nt)])
    #F1 = np.array([np.interp(t_real[i], t_, F1_) for i in  range(nt)])
    #F2 = np.array([np.interp(t_real[i], t_, F2_) for i in  range(nt)])
    #F3 = np.array([np.interp(t_real[i], t_, F3_) for i in  range(nt)])
    Qtot = np.array([np.interp(t_real[i], t_, Qtot_) for i in  range(nt)])
    Qpar = np.array([np.interp(t_real[i], t_, Qpar_) for i in  range(nt)])
    Qprp = np.array([np.interp(t_real[i], t_, Qprp_) for i in  range(nt)])

    if ( (ii == 0) and (jj == 0) ):
      for iit in range(nt):
        if (t_real[iit] <= t0turb):
          it0turb = iit
        if (t_real[iit] <= t1turb):
          it1turb = iit
      t = t_real[it0turb:it1turb]
      freq = np.fft.fftfreq(t.shape[-1],dt)
      if (t.shape[-1] % 2 == 0):
        m = t.shape[-1]/2-1
      else:
        m = (t.shape[-1]-1)/2
      freq = freq*2.*np.pi #f -> omega = 2*pi*f


    #dB1 = B1 - np.mean(B1)
    #dB2 = B2 - np.mean(B2)
    #dB3 = B3 - np.mean(B3)
    #dE1 = E1 - np.mean(E1)
    #dE2 = E2 - np.mean(E2)
    #dE3 = E3 - np.mean(E3)
    #--spectrum
    #B1f = np.fft.fft(dB1[it0turb:it1turb]) / np.float(len(dB1[it0turb:it1turb]))
    #B2f = np.fft.fft(dB2[it0turb:it1turb]) / np.float(len(dB2[it0turb:it1turb]))
    #B3f = np.fft.fft(dB3[it0turb:it1turb]) / np.float(len(dB3[it0turb:it1turb]))
    #E1f = np.fft.fft(dE1[it0turb:it1turb]) / np.float(len(dE1[it0turb:it1turb]))
    #E2f = np.fft.fft(dE2[it0turb:it1turb]) / np.float(len(dE2[it0turb:it1turb]))
    #E3f = np.fft.fft(dE3[it0turb:it1turb]) / np.float(len(dE3[it0turb:it1turb]))
  #  Qtotf = np.abs(np.fft.fft(Qtot[it0turb:-1]))
  #  Qparf = np.abs(np.fft.fft(Qpar[it0turb:-1]))
  #  Qprpf = np.abs(np.fft.fft(Qprp[it0turb:-1]))
    Qtotf = np.fft.fft(Qtot[it0turb:-1])
    Qparf = np.fft.fft(Qpar[it0turb:-1])
    Qprpf = np.fft.fft(Qprp[it0turb:-1])

    #--power spectrum
    #sBparaf_ = np.abs(B1f)*np.abs(B1f)
    #sEparaf_ = np.abs(E1f)*np.abs(E1f)
    #sBperpf_ = np.abs(B2f)*np.abs(B2f) + np.abs(B3f)*np.abs(B3f)
    #sEperpf_ = np.abs(E2f)*np.abs(E2f) + np.abs(E3f)*np.abs(E3f)
    sQtotf_ = np.abs(Qtotf)*np.abs(Qtotf)
    sQparf_ = np.abs(Qparf)*np.abs(Qparf)
    sQprpf_ = np.abs(Qprpf)*np.abs(Qprpf)   

    if ( (ii == 0) and (jj == 0) ):
      #arrays with different spacecrafts
      #sBparaf_all_ = np.zeros([len(sBparaf_),len(id_particle),len(id_proc)]) 
      #sBperpf_all_ = np.zeros([len(sBperpf_),len(id_particle),len(id_proc)])
      #sEparaf_all_ = np.zeros([len(sEparaf_),len(id_particle),len(id_proc)])
      #sEperpf_all_ = np.zeros([len(sEperpf_),len(id_particle),len(id_proc)])
    #  Qtotf_all = np.zeros([len(Qtotf),len(id_particle),len(id_proc)])
    #  Qparf_all = np.zeros([len(Qparf),len(id_particle),len(id_proc)])
    #  Qprpf_all = np.zeros([len(Qprpf),len(id_particle),len(id_proc)])
      sQtotf_all = np.zeros([len(sQtotf_),len(id_particle),len(id_proc)])
      sQparf_all = np.zeros([len(sQparf_),len(id_particle),len(id_proc)])
      sQprpf_all = np.zeros([len(sQprpf_),len(id_particle),len(id_proc)])
      #sBparaf_avg_ = np.zeros(len(sBparaf_))
      #sBperpf_avg_ = np.zeros(len(sBperpf_))
      #sEparaf_avg_ = np.zeros(len(sEparaf_))
      #sEperpf_avg_ = np.zeros(len(sEperpf_))
    #  Qtotf_avg_ = np.zeros(len(Qtotf)) 
    #  Qparf_avg_ = np.zeros(len(Qparf)) 
    #  Qprpf_avg_ = np.zeros(len(Qprpf))
      sQtotf_avg_ = np.zeros(len(sQtotf_))
      sQparf_avg_ = np.zeros(len(sQparf_))
      sQprpf_avg_ = np.zeros(len(sQprpf_))

    #sBparaf_all_[:,jj,ii] = sBparaf_
    #sBperpf_all_[:,jj,ii] = sBperpf_
    #sEparaf_all_[:,jj,ii] = sEparaf_
    #sEperpf_all_[:,jj,ii] = sEperpf_
  #  Qtotf_all[:,jj,ii] = Qtotf
  #  Qparf_all[:,jj,ii] = Qparf
  #  Qprpf_all[:,jj,ii] = Qprpf
    sQtotf_all[:,jj,ii] = sQtotf_
    sQparf_all[:,jj,ii] = sQparf_
    sQprpf_all[:,jj,ii] = sQprpf_

  
    #for kk in range(len(sBparaf_)):
      #sBparaf_avg_[kk] = sBparaf_avg_[kk] + sBparaf_[kk]/Nparticle 
      #sBperpf_avg_[kk] = sBperpf_avg_[kk] + sBperpf_[kk]/Nparticle
      #sEparaf_avg_[kk] = sEparaf_avg_[kk] + sEparaf_[kk]/Nparticle
      #sEperpf_avg_[kk] = sEperpf_avg_[kk] + sEperpf_[kk]/Nparticle 
  #  for kk in range(len(Qtotf)):
  #    Qtotf_avg_[kk] = Qtotf_avg_[kk] + Qtotf[kk]/Nparticle 
  #    Qparf_avg_[kk] = Qparf_avg_[kk] + Qparf[kk]/Nparticle    
  #    Qprpf_avg_[kk] = Qprpf_avg_[kk] + Qprpf[kk]/Nparticle    
    for kk in range(len(sQtotf_)):
      sQtotf_avg_[kk] = sQtotf_avg_[kk] + sQtotf_[kk]/Nparticle
      sQparf_avg_[kk] = sQparf_avg_[kk] + sQparf_[kk]/Nparticle
      sQprpf_avg_[kk] = sQprpf_avg_[kk] + sQprpf_[kk]/Nparticle


#sBparaf_avg = sBparaf_avg_[0:m]
#sEparaf_avg = sEparaf_avg_[0:m]
#sBperpf_avg = sBperpf_avg_[0:m]
#sEperpf_avg = sEperpf_avg_[0:m]
# Qtotf_avg = Qtotf_avg_[0:m]
# Qparf_avg = Qparf_avg_[0:m]
# Qprpf_avg = Qprpf_avg_[0:m]
sQtotf_avg = sQtotf_avg_[0:m]
sQparf_avg = sQparf_avg_[0:m]
sQprpf_avg = sQprpf_avg_[0:m]

for ii in range(m-1):
  #sBparaf_avg[ii+1] = sBparaf_avg[ii+1] + sBparaf_avg_[len(sBparaf_avg_)-1-m]
  #sEparaf_avg[ii+1] = sEparaf_avg[ii+1] + sEparaf_avg_[len(sEparaf_avg_)-1-m]
  #sBperpf_avg[ii+1] = sBperpf_avg[ii+1] + sBperpf_avg_[len(sBperpf_avg_)-1-m]
  #sEperpf_avg[ii+1] = sEperpf_avg[ii+1] + sEperpf_avg_[len(sEperpf_avg_)-1-m]
#  Qtotf_avg[ii+1] = Qtotf_avg[ii+1] + Qtotf_avg_[len(Qtotf_avg_)-1-m]
#  Qparf_avg[ii+1] = Qparf_avg[ii+1] + Qparf_avg_[len(Qparf_avg_)-1-m]
#  Qprpf_avg[ii+1] = Qprpf_avg[ii+1] + Qprpf_avg_[len(Qprpf_avg_)-1-m]
  sQtotf_avg[ii+1] = sQtotf_avg[ii+1] + sQtotf_avg_[len(sQtotf_avg_)-1-m]
  sQparf_avg[ii+1] = sQparf_avg[ii+1] + sQparf_avg_[len(sQparf_avg_)-1-m]
  sQprpf_avg[ii+1] = sQprpf_avg[ii+1] + sQprpf_avg_[len(sQprpf_avg_)-1-m]




print '\n -> omega_max / Omega_ci = ',freq[m]


#plot ranges
xr_min = 0.9*freq[1]
xr_max = freq[m]
#yr_min = 0.5*np.min([np.min(sBparaf_avg),np.min(sBperpf_avg),np.min(sEparaf_avg),np.min(sEperpf_avg)])  #2e-12
#yr_max = 2.0*np.max([np.max(sBparaf_avg),np.max(sBperpf_avg),np.max(sEparaf_avg),np.max(sEperpf_avg)]) #2e-3
# yr_min = 0.5*np.min([np.min(Qtotf_avg),np.min(Qparf_avg),np.min(Qprpf_avg)])  
# yr_max = 2.0*np.max([np.max(Qtotf_avg),np.max(Qparf_avg),np.max(Qprpf_avg)])
yr_min = 0.5*np.min([np.min(sQtotf_avg),np.min(sQparf_avg),np.min(sQprpf_avg)])
yr_max = 2.0*np.max([np.max(sQtotf_avg),np.max(sQparf_avg),np.max(sQprpf_avg)])
# yr_min = 1.33*np.min([np.min(Qtotf_avg),np.min(Qparf_avg),np.min(Qprpf_avg)])  
# yr_max = 1.33*np.max([np.max(Qtotf_avg),np.max(Qparf_avg),np.max(Qprpf_avg)])
#f_mask
f_mask = 6.0 #100.0
#
fig1 = plt.figure(figsize=(8, 7))
grid = plt.GridSpec(7, 7, hspace=0.0, wspace=0.0)
#--spectrum vs freq
ax1a = fig1.add_subplot(grid[0:7,0:7])
#plt.scatter(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sBparaf_avg[1:m],color='c',s=1.5)
#plt.plot(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sBparaf_avg[1:m],'c',linewidth=1,label=r"$\mathcal{E}_{B_z}$")
#plt.scatter(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sEparaf_avg[1:m],color='orange',s=1.5)
#plt.plot(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sEparaf_avg[1:m],'orange',linewidth=1,label=r"$\mathcal{E}_{E_z}$")
#plt.scatter(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sBperpf_avg[1:m],color='b',s=1.5)
#plt.plot(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sBperpf_avg[1:m],'b',linewidth=1,label=r"$\mathcal{E}_{B_\perp}$")
#plt.scatter(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sEperpf_avg[1:m],color='r',s=1.5)
#plt.plot(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sEperpf_avg[1:m],'r',linewidth=1,label=r"$\mathcal{E}_{E_\perp}$")
plt.scatter(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sQtotf_avg[1:m],color='k',s=1.5)
plt.plot(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sQtotf_avg[1:m],'k',linewidth=1,label=r"$\mathcal{E}_{\mathbf{v}\cdot\mathbf{E}}$")
plt.scatter(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sQprpf_avg[1:m],color='b',s=1.5)
plt.plot(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sQprpf_avg[1:m],'b',linewidth=1,label=r"$\mathcal{E}_{\mathbf{v}_\perp\cdot\mathbf{E}_\perp}$")
plt.scatter(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sQparf_avg[1:m],color='r',s=1.5)
plt.plot(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sQparf_avg[1:m],'r',linewidth=1,label=r"$\mathcal{E}_{v_\parallel E_\parallel}$")
# plt.scatter(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),Qtotf_avg[1:m],color='k',s=1.5)
# plt.plot(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),Qtotf_avg[1:m],'k',linewidth=1,label=r"$\mathbf{v}\cdot\mathbf{E}$")
# plt.scatter(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),Qprpf_avg[1:m],color='b',s=1.5)
# plt.plot(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),Qprpf_avg[1:m],'b',linewidth=1,label=r"$\mathbf{v}_\perp\cdot\mathbf{E}_\perp$")
# plt.scatter(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),Qparf_avg[1:m],color='r',s=1.5)
# plt.plot(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),Qparf_avg[1:m],'r',linewidth=1,label=r"$v_\parallel E_\parallel$")
plt.axvline(x=1.0,c='k',ls=':',linewidth=1.5)
plt.axvline(x=2.0,c='k',ls=':',linewidth=1.5)
plt.axvline(x=3.0,c='k',ls=':',linewidth=1.5)
#plt.plot(freq[1:m],1e-6*np.power(freq[1:m],-5./3.),'k--',linewidth=1.5,label=r"$f^{\,-5/3}$")
#plt.plot(freq[1:m],2e-8*np.power(freq[1:m],-2./3.),'k:',linewidth=2,label=r"$f^{\,-2/3}$")
#plt.plot(freq[1:m],5e-8*np.power(freq[1:m],-8./3.),'k-.',linewidth=2,label=r"$f^{\,-8/3}$")
#plt.plot(freq[1:m],2e-7*np.power(freq[1:m],-2.0),'k--',linewidth=1.5,label=r"$f^{\,-2}$")
#plt.plot(freq[1:m],2e-8*np.power(freq[1:m],-1./2.),'k:',linewidth=2,label=r"$f^{\,-1/2}$")
plt.xlim(xr_min,xr_max)
plt.ylim(yr_min,yr_max)
plt.xscale("log")
plt.yscale("log")
ax1a.tick_params(labelsize=15)
plt.title(r'heating vs frequency (tracked particle frame)',fontsize=18)
#plt.xlabel(r'$2\pi f / \Omega_{ci}$',fontsize=17)
plt.xlabel(r'$\omega / \Omega_{ci}$',fontsize=17)
#plt.ylabel(r'slope',fontsize=17)
plt.legend(loc='lower left',markerscale=4,frameon=False,fontsize=16,ncol=1)
#--show and/or save
plt.show()
#plt.tight_layout()
#flnm = prob+".HeatingPowerSpectrum-vs-Freq.TrackedParticles.Nparticle"+"%d"%int(Nparticle)+".t-interval."+"%d"%int(round(t_real[it0turb]))+"-"+"%d"%int(round(t_real[it1turb]))
#path_output = path_save+flnm+fig_frmt
#plt.savefig(path_output,bbox_to_inches='tight')#,pad_inches=-1)
#plt.close()
#print " -> figure saved in:",path_output


#plt.plot(freq, B2f.real, freq, B2f.imag)
#plt.plot(freq[1:m],sBf[1:m],'b')
#plt.plot(xnew,sBf_smooth,'k')
#plt.plot(freq[1:m],sEf[1:m],'r')
#plt.plot(xnew,sEf_smooth,'k')
#plt.xscale("log")
#plt.yscale("log")
#plt.show()

print "\n"

