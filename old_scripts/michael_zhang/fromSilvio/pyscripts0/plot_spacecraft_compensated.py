import re
import warnings
from io import open  # Consistent binary I/O from Python 2 and 3
import numpy as np
import pegasus_read as pegr
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib.pyplot import *
from scipy.interpolate import spline
import derivatives as derivs
from scipy.ndimage.filters import gaussian_filter1d

#--time interval (\Omega_ci^{-1} units)
t0turb = 650.0
t1turb = 1141.0

#--physical parameters
betai0 = 1./9.              # ion plasma beta
TeTi = 1.0                  # temperature ratio (Te/Ti)
beta0 = (1.+TeTi)*betai0    # total beta (beta0 = betai0 + betae0)
omega_drift = 1.1 * betai0  # ion drift frequency (gradB or curvature, with <beta>_turb ~ 1.1*beta_0)

#--fit method
#fit_method = 'logspaced_gradient' 
fit_method = 'local_slope_manual'

#--fit parameter 
n_pt = 25 #20 #6
n_logbins = 100 #50 #100

#--smooth plot?
smoothed_plot = False #True

#--gaussian smoothing
sigma_smoothing = 2

#--stationary spacecraft IDs
id_spcrft = [0,11,22,33,44,55,66,77,88,100]
Nspcrft = np.float(len(id_spcrft))

#--plot's masked frequencies (f > f_mask)
f_mask = 10.0 #20.0 #100.0
f_mask_slope = 4.0

#--figure format
fig_frmt = ".png"

#--box parameters
tcorr = 24.0             # forcing time correlation (\Omega_ci^{-1} units)
tcross = 2.0*np.pi*tcorr # crossing time (\Omega_ci^{-1} units)
aspct = 6
lprp = 4.0               # in (2*pi*d_i) units
lprl = lprp*aspct        # in (2*pi*d_i) units 
Lperp = 2.0*np.pi*lprp   # in d_i units
Lpara = 2.0*np.pi*lprl   # in d_i units 
N_perp = 288
N_para = N_perp*aspct    # assuming isotropic resolution 
kperpdi0 = 1./lprp       # minimum k_perp ( = 2*pi / Lperp) 
kparadi0 = 1./lprl       # minimum k_para ( = 2*pi / Lpara)

#--rho_i units and KAW eigenvector normalization for density spectrum
kperprhoi0 = np.sqrt(betai0)*kperpdi0
kpararhoi0 = np.sqrt(betai0)*kparadi0
normKAW = betai0*(1.+betai0)*(1. + 1./(1. + 1./betai0))

#--IO options 
path_read = "../spacecraft/"
path_save = "../figures/"
prob = "turb"
fig_frmt = ".png"

#--latex fonts
font = 11
mpl.rc('text', usetex=True)
mpl.rcParams['text.latex.preamble']=[r"\usepackage{amsmath}"]
mpl.rc('font', family = 'serif', size = font)


for ii in range(len(id_spcrft)):
  data = pegr.spacecraft_read(path_read,prob,id_spcrft[ii])

#spacecraft files keywords
# [1]=time     [2]=x1       [3]=x2       [4]=x3       [5]=v1       [6]=v2       [7]=v3       [8]=B1       [9]=B2       [10]=B3       [11]=E1       [12]=E2       [13]=E3       [14]=U1       [15]=U2       [16]=U3       [17]=dens     [18]=F1       [19]=F2       [20]=F3


  t_ = data[u'time']
  #x1_ = data[u'x1']
  #x2_ = data[u'x2']
  #x3_ = data[u'x3']
  #v1_ = data[u'v1']
  #v2_ = data[u'v2']
  #v3_ = data[u'v3']
  B1_ = data[u'B1']
  B2_ = data[u'B2']
  B3_ = data[u'B3']
  E1_ = data[u'E1']
  E2_ = data[u'E2']
  E3_ = data[u'E3']
  U1_ = data[u'U1']
  U2_ = data[u'U2']
  U3_ = data[u'U3']
  Dn_ = data[u'dens']
  #F1_ = data[u'F1']
  #F2_ = data[u'F2']
  #F3_ = data[u'F3']

  if (ii == 0):
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
  B1 = np.array([np.interp(t_real[i], t_, B1_) for i in  range(nt)])
  B2 = np.array([np.interp(t_real[i], t_, B2_) for i in  range(nt)])
  B3 = np.array([np.interp(t_real[i], t_, B3_) for i in  range(nt)])
  E1 = np.array([np.interp(t_real[i], t_, E1_) for i in  range(nt)])
  E2 = np.array([np.interp(t_real[i], t_, E2_) for i in  range(nt)])
  E3 = np.array([np.interp(t_real[i], t_, E3_) for i in  range(nt)])
  #U1 = np.array([np.interp(t_real[i], t_, U1_) for i in  range(nt)])
  #U2 = np.array([np.interp(t_real[i], t_, U2_) for i in  range(nt)])
  #U3 = np.array([np.interp(t_real[i], t_, U3_) for i in  range(nt)])
  Dn = np.array([np.interp(t_real[i], t_, Dn_) for i in  range(nt)])
  #F1 = np.array([np.interp(t_real[i], t_, F1_) for i in  range(nt)])
  #F2 = np.array([np.interp(t_real[i], t_, F2_) for i in  range(nt)])
  #F3 = np.array([np.interp(t_real[i], t_, F3_) for i in  range(nt)])

  if (ii == 0):
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


  dB1 = B1 - np.mean(B1)
  dB2 = B2 - np.mean(B2)
  dB3 = B3 - np.mean(B3)
  dE1 = E1 - np.mean(E1)
  dE2 = E2 - np.mean(E2)
  dE3 = E3 - np.mean(E3)
  #dU1 = U1 - np.mean(U1)
  #dU2 = U2 - np.mean(U2)
  #dU3 = U3 - np.mean(U3)
  dDn = Dn - np.mean(Dn)
  B1f = np.fft.fft(dB1[it0turb:it1turb]) / np.float(len(dB1[it0turb:it1turb]))
  B2f = np.fft.fft(dB2[it0turb:it1turb]) / np.float(len(dB2[it0turb:it1turb]))
  B3f = np.fft.fft(dB3[it0turb:it1turb]) / np.float(len(dB3[it0turb:it1turb]))
  E1f = np.fft.fft(dE1[it0turb:it1turb]) / np.float(len(dE1[it0turb:it1turb]))
  E2f = np.fft.fft(dE2[it0turb:it1turb]) / np.float(len(dE2[it0turb:it1turb]))
  E3f = np.fft.fft(dE3[it0turb:it1turb]) / np.float(len(dE3[it0turb:it1turb]))
  #U1f = np.fft.fft(dU1[it0turb:it1turb]) / np.float(len(dU1[it0turb:it1turb]))
  #U2f = np.fft.fft(dU2[it0turb:it1turb]) / np.float(len(dU2[it0turb:it1turb]))
  #U3f = np.fft.fft(dU3[it0turb:it1turb]) / np.float(len(dU3[it0turb:it1turb]))
  Dnf = np.fft.fft(dDn[it0turb:it1turb]) / np.float(len(dDn[it0turb:it1turb]))

  sBparaf_ = np.abs(B1f)*np.abs(B1f)
  sEparaf_ = np.abs(E1f)*np.abs(E1f)
  #sUparaf_ = np.abs(U1f)*np.abs(U1f)
  sBperpf_ = np.abs(B2f)*np.abs(B2f) + np.abs(B3f)*np.abs(B3f)
  sEperpf_ = np.abs(E2f)*np.abs(E2f) + np.abs(E3f)*np.abs(E3f)
  #sUperpf_ = np.abs(U2f)*np.abs(U2f) + np.abs(U3f)*np.abs(U3f)
  sDnf_ = np.abs(Dnf)*np.abs(Dnf) 

  if (ii == 0): 
    #arrays with different spacecrafts
    sBparaf_all_ = np.zeros([len(sBparaf_),len(id_spcrft)]) 
    sBperpf_all_ = np.zeros([len(sBperpf_),len(id_spcrft)]) 
    sEparaf_all_ = np.zeros([len(sEparaf_),len(id_spcrft)]) 
    sEperpf_all_ = np.zeros([len(sEperpf_),len(id_spcrft)]) 
    #sUparaf_all_ = np.zeros([len(sUparaf_),len(id_spcrft)])
    #sUperpf_all_ = np.zeros([len(sUperpf_),len(id_spcrft)])
    sDnf_all_ = np.zeros([len(sDnf_),len(id_spcrft)])
    #
    sBparaf_avg_ = np.zeros(len(sBparaf_))
    sBperpf_avg_ = np.zeros(len(sBperpf_))
    sEparaf_avg_ = np.zeros(len(sEparaf_))
    sEperpf_avg_ = np.zeros(len(sEperpf_))
    #sUparaf_avg_ = np.zeros(len(sUparaf_))
    #sUperpf_avg_ = np.zeros(len(sUperpf_))
    sDnf_avg_ = np.zeros(len(sDnf_))

  sBparaf_all_[:,ii] = sBparaf_
  sBperpf_all_[:,ii] = sBperpf_
  sEparaf_all_[:,ii] = sEparaf_
  sEperpf_all_[:,ii] = sEperpf_
  #sUparaf_all_[:,ii] = sUparaf_
  #sUperpf_all_[:,ii] = sUperpf_
  sDnf_all_[:,ii] = sDnf_

  for kk in range(len(sBparaf_)):
    sBparaf_avg_[kk] = sBparaf_avg_[kk] + sBparaf_[kk]/Nspcrft 
    sBperpf_avg_[kk] = sBperpf_avg_[kk] + sBperpf_[kk]/Nspcrft 
    sEparaf_avg_[kk] = sEparaf_avg_[kk] + sEparaf_[kk]/Nspcrft 
    sEperpf_avg_[kk] = sEperpf_avg_[kk] + sEperpf_[kk]/Nspcrft 
    #sUparaf_avg_[kk] = sUparaf_avg_[kk] + sUparaf_[kk]/Nspcrft
    #sUperpf_avg_[kk] = sUperpf_avg_[kk] + sUperpf_[kk]/Nspcrft
    sDnf_avg_[kk] = sDnf_avg_[kk] + sDnf_[kk]/Nspcrft


sBparaf_avg = sBparaf_avg_[0:m]
sBperpf_avg = sBperpf_avg_[0:m]
sEparaf_avg = sEparaf_avg_[0:m]
sEperpf_avg = sEperpf_avg_[0:m]
#sUparaf_avg = sUparaf_avg_[0:m]
#sUperpf_avg = sUperpf_avg_[0:m]
sDnf_avg = sDnf_avg_[0:m]

for ii in range(m-1):
  sBparaf_avg[ii+1] = sBparaf_avg[ii+1] + sBparaf_avg_[len(sBparaf_)-1-m]
  sBperpf_avg[ii+1] = sBperpf_avg[ii+1] + sBperpf_avg_[len(sBperpf_)-1-m]
  sEparaf_avg[ii+1] = sEparaf_avg[ii+1] + sEparaf_avg_[len(sEparaf_)-1-m]
  sEperpf_avg[ii+1] = sEperpf_avg[ii+1] + sEperpf_avg_[len(sEperpf_)-1-m]
  #sUparaf_avg[ii+1] = sUparaf_avg[ii+1] + sUparaf_avg_[len(sUparaf_)-1-m]
  #sUperpf_avg[ii+1] = sUperpf_avg[ii+1] + sUperpf_avg_[len(sUperpf_)-1-m]
  sDnf_avg[ii+1] = sDnf_avg[ii+1] + sDnf_avg_[len(sDnf_)-1-m]


#smoothing spectra for fitting slopes
sBparaf_avg_smooth = gaussian_filter1d(sBparaf_avg, sigma=sigma_smoothing)
sBperpf_avg_smooth = gaussian_filter1d(sBperpf_avg, sigma=sigma_smoothing)
sEparaf_avg_smooth = gaussian_filter1d(sEparaf_avg, sigma=sigma_smoothing)
sEperpf_avg_smooth = gaussian_filter1d(sEperpf_avg, sigma=sigma_smoothing)
sDnf_avg_smooth = gaussian_filter1d(sDnf_avg, sigma=sigma_smoothing)


print '\n -> omega_max / Omega_ci = ',freq[m]
print '\n -> frequency modes: ',m

print "\n [ computing local slopes ]"

#--arrays containing local spectral slope
#k_perp
aBperpfreq = np.zeros(len(sBperpf_avg_smooth))
aBparafreq = np.zeros(len(sBparaf_avg_smooth))
aEperpfreq = np.zeros(len(sEperpf_avg_smooth))
aEparafreq = np.zeros(len(sEparaf_avg_smooth))
aDnfreq = np.zeros(len(sDnf_avg_smooth))

#--progressive fit in the range of frequency where there are no n_pt points on the left
#--NOTE: we do not evaluate slope in the first two points, and we do not include the firts point in the fits 
f_fit = freq[0:m]
Bperpf_fit = sBperpf_avg_smooth
Bparaf_fit = sBparaf_avg_smooth
Eperpf_fit = sEperpf_avg_smooth 
Eparaf_fit = sEparaf_avg_smooth
Dnf_fit = sDnf_avg_smooth 
###--first (n_pt-1) points in both k_perp and k_para: progressive fit
#for jj in range(n_pt):
#  aBperpfreq[jj+2],c = np.polyfit(np.log10(f_fit[1:2*(2+jj)]),np.log10(Bperpf_fit[1:2*(2+jj)]),1)
#  aBparafreq[jj+2],c = np.polyfit(np.log10(f_fit[1:2*(2+jj)]),np.log10(Bparaf_fit[1:2*(2+jj)]),1)
#  aEperpfreq[jj+2],c = np.polyfit(np.log10(f_fit[1:2*(2+jj)]),np.log10(Eperpf_fit[1:2*(2+jj)]),1)
#  aEparafreq[jj+2],c = np.polyfit(np.log10(f_fit[1:2*(2+jj)]),np.log10(Eparaf_fit[1:2*(2+jj)]),1)
#  aDnfreq[jj+2],c = np.polyfit(np.log10(f_fit[1:2*(2+jj)]),np.log10(Dnf_fit[1:2*(2+jj)]),1)
##fit of the remaining k_perp range using [ f0 - n_pt, f0 + n_pt ] points to determine the slope in f0
#for jj in range(1,len(f_fit)-2*n_pt):
#  aBperpfreq[jj+n_pt],c = np.polyfit(np.log10(f_fit[jj:jj+2*n_pt+1]),np.log10(Bperpf_fit[jj:jj+2*n_pt+1]),1)
#  aBparafreq[jj+n_pt],c = np.polyfit(np.log10(f_fit[jj:jj+2*n_pt+1]),np.log10(Bparaf_fit[jj:jj+2*n_pt+1]),1)
#  aEperpfreq[jj+n_pt],c = np.polyfit(np.log10(f_fit[jj:jj+2*n_pt+1]),np.log10(Eperpf_fit[jj:jj+2*n_pt+1]),1)
#  aEparafreq[jj+n_pt],c = np.polyfit(np.log10(f_fit[jj:jj+2*n_pt+1]),np.log10(Eparaf_fit[jj:jj+2*n_pt+1]),1)
#  aDnfreq[jj+n_pt],c = np.polyfit(np.log10(f_fit[jj:jj+2*n_pt+1]),np.log10(Dnf_fit[jj:jj+2*n_pt+1]),1)

if (fit_method == 'local_slope_manual'):
  for jj in range(3,len(f_fit)-2*n_pt):
    if (jj < n_pt):
      #--odd indices
      i_npt = jj-1 
      aBperpfreq[jj+i_npt],c = np.polyfit(np.log10(f_fit[jj:jj+2*i_npt+1]),np.log10(Bperpf_fit[jj:jj+2*i_npt+1]),1)
      aBparafreq[jj+i_npt],c = np.polyfit(np.log10(f_fit[jj:jj+2*i_npt+1]),np.log10(Bparaf_fit[jj:jj+2*i_npt+1]),1)
      aEperpfreq[jj+i_npt],c = np.polyfit(np.log10(f_fit[jj:jj+2*i_npt+1]),np.log10(Eperpf_fit[jj:jj+2*i_npt+1]),1)
      aEparafreq[jj+i_npt],c = np.polyfit(np.log10(f_fit[jj:jj+2*i_npt+1]),np.log10(Eparaf_fit[jj:jj+2*i_npt+1]),1)
      aDnfreq[jj+i_npt],c = np.polyfit(np.log10(f_fit[jj:jj+2*i_npt+1]),np.log10(Dnf_fit[jj:jj+2*i_npt+1]),1)
      #--even indices
      i_npt = jj
      aBperpfreq[jj+i_npt],c = np.polyfit(np.log10(f_fit[jj:jj+2*i_npt+1]),np.log10(Bperpf_fit[jj:jj+2*i_npt+1]),1)
      aBparafreq[jj+i_npt],c = np.polyfit(np.log10(f_fit[jj:jj+2*i_npt+1]),np.log10(Bparaf_fit[jj:jj+2*i_npt+1]),1)
      aEperpfreq[jj+i_npt],c = np.polyfit(np.log10(f_fit[jj:jj+2*i_npt+1]),np.log10(Eperpf_fit[jj:jj+2*i_npt+1]),1)
      aEparafreq[jj+i_npt],c = np.polyfit(np.log10(f_fit[jj:jj+2*i_npt+1]),np.log10(Eparaf_fit[jj:jj+2*i_npt+1]),1)
      aDnfreq[jj+i_npt],c = np.polyfit(np.log10(f_fit[jj:jj+2*i_npt+1]),np.log10(Dnf_fit[jj:jj+2*i_npt+1]),1)
    else:
      aBperpfreq[jj+n_pt],c = np.polyfit(np.log10(f_fit[jj:jj+2*n_pt+1]),np.log10(Bperpf_fit[jj:jj+2*n_pt+1]),1)
      aBparafreq[jj+n_pt],c = np.polyfit(np.log10(f_fit[jj:jj+2*n_pt+1]),np.log10(Bparaf_fit[jj:jj+2*n_pt+1]),1)
      aEperpfreq[jj+n_pt],c = np.polyfit(np.log10(f_fit[jj:jj+2*n_pt+1]),np.log10(Eperpf_fit[jj:jj+2*n_pt+1]),1)
      aEparafreq[jj+n_pt],c = np.polyfit(np.log10(f_fit[jj:jj+2*n_pt+1]),np.log10(Eparaf_fit[jj:jj+2*n_pt+1]),1)
      aDnfreq[jj+n_pt],c = np.polyfit(np.log10(f_fit[jj:jj+2*n_pt+1]),np.log10(Dnf_fit[jj:jj+2*n_pt+1]),1)
  #arrays for cleaned local spectral slopes
  freq_fit = np.array([])
  aBperpf = np.array([])
  aBparaf = np.array([])
  aEperpf = np.array([])
  aEparaf = np.array([])
  aDnf = np.array([])
  #cleaned local specral slope vs freq
  for jj in range(len(aBperpfreq)):
    if ( (np.abs(aBperpfreq[jj])>1e-20) and (np.abs(aBparafreq[jj])>1e-20) and (np.abs(aEperpfreq[jj])>1e-20) and (np.abs(aEparafreq[jj])>1e-20) and (np.abs(aDnfreq[jj])>1e-20) ):
      freq_fit = np.append(freq_fit,f_fit[jj])
      aBperpf = np.append(aBperpf,aBperpfreq[jj])
      aBparaf = np.append(aBparaf,aBparafreq[jj])
      aEperpf = np.append(aEperpf,aEperpfreq[jj])
      aEparaf = np.append(aEparaf,aEparafreq[jj])
      aDnf = np.append(aDnf,aDnfreq[jj])



if (fit_method == 'logspaced_gradient'):
  f_logspaced = np.logspace(np.log10(f_fit[4]),np.log10(f_fit[len(f_fit)-1]),num=n_logbins)
  print f_logspaced
  df_logspaced = np.log10(f_logspaced[1])-np.log10(f_logspaced[0])
  print df_logspaced
  Bperpf_logspaced = np.interp(f_logspaced,f_fit,Bperpf_fit)
  Bparaf_logspaced = np.interp(f_logspaced,f_fit,Bparaf_fit)
  Eperpf_logspaced = np.interp(f_logspaced,f_fit,Eperpf_fit)
  Eparaf_logspaced = np.interp(f_logspaced,f_fit,Eparaf_fit)
  Dnf_logspaced = np.interp(f_logspaced,f_fit,Dnf_fit)
  #aBperpfreq = np.gradient(np.log10(Bperpf_logspaced),np.log10(f_logspaced))
  #aBparafreq = np.gradient(np.log10(Bparaf_logspaced),np.log10(f_logspaced))
  #aEperpfreq = np.gradient(np.log10(Eperpf_logspaced),np.log10(f_logspaced))
  #aEparafreq = np.gradient(np.log10(Eparaf_logspaced),np.log10(f_logspaced))
  #aDnfreq = np.gradient(np.log10(Dnf_logspaced),np.log10(f_logspaced))
  #
  aBperpfreq = np.gradient(np.log10(Bperpf_logspaced),df_logspaced)
  aBparafreq = np.gradient(np.log10(Bparaf_logspaced),df_logspaced)
  aEperpfreq = np.gradient(np.log10(Eperpf_logspaced),df_logspaced)
  aEparafreq = np.gradient(np.log10(Eparaf_logspaced),df_logspaced)
  aDnfreq = np.gradient(np.log10(Dnf_logspaced),df_logspaced)
  #
  #aBperpfreq = derivs.gradientO4(np.log10(Bperpf_logspaced),df_logspaced)
  #aBparafreq = derivs.gradientO4(np.log10(Bparaf_logspaced),df_logspaced)
  #aEperpfreq = derivs.gradientO4(np.log10(Eperpf_logspaced),df_logspaced)
  #aEparafreq = derivs.gradientO4(np.log10(Eparaf_logspaced),df_logspaced)
  #aDnfreq = derivs.gradientO4(np.log10(Dnf_logspaced),df_logspaced)
  #
  f_fit = f_logspaced
  #
  freq_fit = f_fit 
  aBperpf = aBperpfreq 
  aBparaf = aBparafreq
  aEperpf = aEperpfreq
  aEparaf = aEparafreq
  aDnf = aDnfreq 
  print aBperpf



#--compute spectral ratios
print "\n [ computing spectral ratios ]"
# r1(k_perp) = [ 2*(1+beta) / beta ] * dBpara(k_perp)^2 / dB(kperp)^2
#r1 = ( 2.0*(1.0+beta0)/beta0 )*Bprlkprp/Bkprp 
# r1(k_perp) = [ beta^2 / 4 ] * dn(k_perp)^2 / dBpara(k_perp)^2
r2 = ( beta0**2.0 / 4.0 )*sDnf_avg/sBparaf_avg 
# r3(k_perp) = [ (2+beta)/beta ] * dBpara(k_perp)^2 / dBperp(k_perp)^2
r3 = ( (2.0+beta0) / beta0 )*sBparaf_avg/sBperpf_avg
# r4(k_perp) = [ beta*(2+beta) / 4 ] * dn(k_perp)^2 / dBperp(k_perp)^2
r4 = ( beta0*(2.0+beta0) / 4.0 )*sDnf_avg/sBperpf_avg 
# r5(k_perp) =  dEperp(k_perp)^2 / dBperp(k_perp)^2
r5 = sEperpf_avg / sBperpf_avg





print "\n [ producing figure ]\n"
font_size = 19
line_thick = 3.5
slope_thick = 2.5
#plot ranges
xr_min = 0.9*freq[1]
xr_max = np.min([freq[m],f_mask])
#yr_min = 1.e-9 #0.5*np.min([np.min(sBparaf_avg),np.min(sBperpf_avg),np.min(sEperpf_avg),np.min(normKAW*sDnf_avg)])
yr_min = 2.e-7
#yr_max = 2.e-3 #2.0*np.max([np.max(sBparaf_avg),np.max(sBperpf_avg),np.max(sEperpf_avg),np.max(normKAW*sDnf_avg)])
yr_max = 3.e-6
yr_min_s = -6
yr_max_s = -1./3. #+0.75
yr_min_r5 = 7e-1
yr_max_r5 = 4e+2
yr_min_r3 = 1e-1
yr_max_r3 = 2e+1
yr_min_r2 = 1.25e-2
yr_max_r2 = 2.5e+0
#
fig1 = plt.figure(figsize=(9, 9))
grid = plt.GridSpec(9, 1, hspace=0.0, wspace=0.0)
#--spectrum vs frequency 
ax1a = fig1.add_subplot(grid[0:6,0:1])
#plt.scatter(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sBperpf_avg[1:m],color='b',s=2.5)
if smoothed_plot:
  p1a, = plt.plot(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),gaussian_filter1d((freq[1:m]**2.)*sBperpf_avg[1:m],sigma=sigma_smoothing),'b',linewidth=line_thick,label=r"$\omega^2\mathcal{E}_{B_\perp}$")
else:
  p1a, = plt.plot(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),(freq[1:m]**2.)*sBperpf_avg[1:m],'b',linewidth=line_thick,label=r"$\omega^2\mathcal{E}_{B_\perp}$")
#plt.scatter(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sBparaf_avg[1:m],color='c',s=2.5)
##p2a, = plt.plot(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sBparaf_avg[1:m],'c',linewidth=line_thick,label=r"$\mathcal{E}_{B_z}$")
#plt.scatter(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sEperpf_avg[1:m],color='r',s=2.5)
##p3a, = plt.plot(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sEperpf_avg[1:m],'r',linewidth=line_thick,label=r"$\mathcal{E}_{E_\perp}$")
#plt.scatter(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sEparaf_avg[1:m],color='orange',s=1.5)
#p4a, = plt.plot(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),sEparaf_avg[1:m],'orange',linewidth=1,label=r"$\mathcal{E}_{E_z}$")
#plt.scatter(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),normKAW*sDnf_avg[1:m],color='g',s=2.5)
##p5a, = plt.plot(np.ma.masked_where(freq[1:m] > f_mask, freq[1:m]),normKAW*sDnf_avg[1:m],'g',linewidth=line_thick,label=r"$\mathcal{E}_{\widetilde{n}}$")
#plt.scatter(f_logspaced,Bperpf_logspaced,color='k',s=30)
plt.axvline(x=1.0,c='k',ls=':',linewidth=slope_thick)
plt.axvline(x=2.0,c='k',ls=':',linewidth=slope_thick)
plt.axvline(x=3.0,c='k',ls=':',linewidth=slope_thick)
#plt.axvline(x=4.0,c='k',ls=':',linewidth=1.5)
#plt.axvline(x=5.0,c='k',ls=':',linewidth=1.5)
plt.axvline(x=omega_drift,c='m',ls=':',linewidth=slope_thick)
#plt.text(1.1*omega_drift,2.*yr_min,r'$\omega/\Omega_{\mathrm{c,i}}\sim\langle\beta_{\mathrm{i}}\rangle_{\mathrm{turb}}$',va='bottom',ha='left',color='m',rotation=90,fontsize=16)
plt.text(1.1*omega_drift,1.2*yr_min,r'$\omega = \omega_{\mathrm{D}}$',va='bottom',ha='left',color='m',rotation=90,fontsize=font_size)
#p6a, = plt.plot(freq[1:m],sBperpf_avg[8]*np.power(freq[1:m]/freq[8],-2.0),'k--',linewidth=slope_thick,label=r"$\omega^{\,-2}$")
#p7a, = plt.plot(freq[1:m],sBperpf_avg[np.where(freq > 2.0)[0][0]]*np.power(freq[1:m]/2.0,-4.0),'k-.',linewidth=slope_thick,label=r"$\omega^{\,-4}$")
p8a, = plt.plot(freq[1:m],sBperpf_avg[8]*(freq[8]**2.)*(freq[1:m]/freq[1:m]),'k--',linewidth=slope_thick,label=r"$\omega^{\,-2}$")
p9a, = plt.plot(freq[1:m],0.6*sBperpf_avg[8]*(freq[8]**2.)*(freq[1:m]/freq[1:m]),'k-.',linewidth=slope_thick,label=r"$\omega^{\,-2}$")
plt.xlim(xr_min,xr_max)
plt.ylim(yr_min,yr_max)
plt.xscale("log")
plt.yscale("log")
ax1a.set_xticklabels('')
ax1a.tick_params(labelsize=font_size)
plt.ylabel(r'$\omega^2\mathcal{E}_{B_\perp}(\omega)$',fontsize=font_size)
#plt.title(r'spectra vs frequency (plasma frame)',fontsize=18)
##l1 = plt.legend([p1a,p2a,p3a,p5a], [r"$\mathcal{E}_{B_\perp}$",r"$\mathcal{E}_{B_z}$",r"$\mathcal{E}_{E_\perp}$",r"$\mathcal{E}_{\widetilde{n}}$"], loc='lower left',markerscale=4,frameon=False,fontsize=font_size,ncol=1)
##l2 = plt.legend([p6a,p7a], [r"$\omega^{-2}$",r"$\omega^{-4}$"], loc='upper right',markerscale=4,frameon=False,fontsize=font_size,ncol=1)
##gca().add_artist(l1)
#l1 = plt.legend([p1a], [r"$\mathcal{E}_{B_\perp}$"], loc='lower left',markerscale=4,frameon=False,fontsize=font_size,ncol=1)
#l2 = plt.legend([p6a,p7a], [r"$\omega^{-2}$",r"$\omega^{-4}$"], loc='upper right',markerscale=4,frameon=False,fontsize=font_size,ncol=1)
l2 = plt.legend([p8a,p9a], [r"$\mathcal{E}_{B_\perp,\mathrm{inj}}$",r"$60\%\mathcal{E}_{B_\perp,\mathrm{inj}}$"], loc='upper left',markerscale=4,frameon=False,fontsize=font_size,ncol=1)
#gca().add_artist(l1)
#--local slopes
ax1b = fig1.add_subplot(grid[6:9,0:1])
plt.scatter(np.ma.masked_where(freq_fit > f_mask_slope, freq_fit),aBperpf,color='b',s=10)
#plt.scatter(np.ma.masked_where(freq_fit > f_mask_slope, freq_fit),aBparaf,color='c',s=10)
#plt.scatter(np.ma.masked_where(freq_fit > f_mask_slope, freq_fit),aEperpf,color='r',s=10)
#plt.scatter(np.ma.masked_where(freq_fit > f_mask_slope, freq_fit),aEparaf,color='orange',s=10)
#plt.scatter(np.ma.masked_where(freq_fit > f_mask_slope, freq_fit),aDnf,color='g',s=10)
plt.axvline(x=1.0,c='k',ls=':',linewidth=slope_thick)
plt.axvline(x=2.0,c='k',ls=':',linewidth=slope_thick)
plt.axvline(x=3.0,c='k',ls=':',linewidth=slope_thick)
#plt.axvline(x=4.0,c='k',ls=':',linewidth=1.5)
#plt.axvline(x=5.0,c='k',ls=':',linewidth=1.5)
plt.axvline(x=omega_drift,c='m',ls=':',linewidth=slope_thick)
plt.axhline(y=-2.0,c='k',ls='--',linewidth=slope_thick)
plt.axhline(y=-4.0,c='k',ls='-.',linewidth=slope_thick)
plt.xlim(xr_min,xr_max)
plt.ylim(yr_min_s,yr_max_s)
plt.xscale("log")
#ax1b.set_xticklabels('')
plt.ylabel(r'Local Slope',fontsize=font_size)
ax1b.tick_params(labelsize=font_size)
#--show and/or save
#plt.show()
plt.tight_layout()
if (fit_method == 'local_slope_manual'):
  if smoothed_plot:
    flnm = prob+".StationarySpacecraftsAvg.FreqSpectrumBperp-Slope.Compensated-smoothed-sigma"+"%d"%sigma_smoothing+".npt"+"%d"%n_pt+".t-interval."+"%d"%int(round(t_real[it0turb]))+"-"+"%d"%int(round(t_real[it1turb]))
  else:
    flnm = prob+".StationarySpacecraftsAvg.FreqSpectrumBperp-Slope.Compensated.npt"+"%d"%n_pt+".t-interval."+"%d"%int(round(t_real[it0turb]))+"-"+"%d"%int(round(t_real[it1turb]))
if (fit_method == 'logspaced_gradient'):
  flnm = prob+".StationarySpacecraftsAvg.FreqSpectrumBperp-Slope.Compensated.nlogbins"+"%d"%n_logbins+".t-interval."+"%d"%int(round(t_real[it0turb]))+"-"+"%d"%int(round(t_real[it1turb]))
path_output = path_save+flnm+fig_frmt
plt.savefig(path_output,bbox_to_inches='tight')#,pad_inches=-1)
plt.close()
print " -> figure saved in:",path_output

 

print "\n"  

