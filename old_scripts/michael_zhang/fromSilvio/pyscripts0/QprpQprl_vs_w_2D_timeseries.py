import numpy as np
import struct
import math
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import matplotlib as mpl
import pegasus_read as pegr
from matplotlib.pyplot import *
from scipy.ndimage import gaussian_filter


#output range
it0 = 1 #65       
it1 = 9 #144 

#cooling corrections
it0corr = 0
it1corr = 25
cooling_corr_perp = True 
cooling_corr_para = False #True

#gaussian filter
apply_smoothing = True
sigma_smoothing = 1 

#verbosity
verb_diag = False
verb_read = False

#v-space binning
Nvperp = 200
Nvpara = 400
vpara_min = -4.0
vpara_max = 4.0
vperp_min = 0.0
vperp_max = 4.0

#number of processors used
n_proc = 384*64

#figure format
output_figure = True 
fig_frmt = ".png"#".pdf"
width_2columns = 512.11743/72.2
width_1column = 245.26653/72.2
width_2columns *= 5./3.
width_1column *= 5./3.

# box parameters (beta = 1/9)
aspct = 6
lprp = 4.0              # in (2*pi*d_i) units
lprl = lprp*aspct       # in (2*pi*d_i) units 
Lperp = 2.0*np.pi*lprp  # in d_i units
Lpara = 2.0*np.pi*lprl  # in d_i units 
N_perp = 288
N_para = N_perp*aspct   # assuming isotropic resolution 
kperpdi0 = 1./lprp      # minimum k_perp ( = 2*pi / Lperp) 
kparadi0 = 1./lprl      # minimum k_para ( = 2*pi / Lpara)
betai0 = 1./9.          # ion plasma beta
#--rho_i units and KAW eigenvector normalization for density spectrum
kperprhoi0 = np.sqrt(betai0)*kperpdi0
kpararhoi0 = np.sqrt(betai0)*kparadi0
normKAW = betai0*(1.+betai0)*(1. + 1./(1. + 1./betai0))
#--alfven speed (v_th units)
vA01 = np.sqrt(1./betai0)
#--d_i scale (rho_th units)
kdi01 = np.sqrt(betai0)

#paths
problem = "turb"
path_read = "../spec_npy/"
path_save = "../figures/"

#latex fonts
font = 9
mpl.rc('text', usetex=True)
mpl.rc('font', family = 'serif')
mpl.rcParams['xtick.labelsize']=font-1
mpl.rcParams['ytick.labelsize']=font-1
mpl.rcParams['text.latex.preamble']=[r"\usepackage{amsmath}"]
mpl.rcParams['contour.negative_linestyle'] = 'solid'

#Hawley colormap
bit_rgb = np.linspace(0,1,256)
colors = [(0,0,127), (0,3,255), (0,255,255), (128,128,128), (255,255,0),(255,0,0),(135,0,0)]
positions = [0.0,0.166667,0.333333,0.5,0.666667,0.833333,1]
for iii in range(len(colors)):
 colors[iii] = (bit_rgb[colors[iii][0]],
                bit_rgb[colors[iii][1]],
                bit_rgb[colors[iii][2]])

cdict = {'red':[], 'green':[], 'blue':[]}
for pos, color in zip(positions, colors):
 cdict['red'].append((pos, color[0], color[0]))
 cdict['green'].append((pos, color[1], color[1]))
 cdict['blue'].append((pos, color[2], color[2]))

cmap = mpl.colors.LinearSegmentedColormap('my_colormap',cdict,256)


time = np.loadtxt('../times.dat')


#reading initial condition
print "\n [ reading initial condition ]"
vdf0, vprp0, vprl0 = pegr.readnpy_vdf(path_read,0,Nvperp,Nvpara,vperp_min,vperp_max,vpara_min,vpara_max,verbose=verb_read)
#
#first normalization by number of processors
vdf0 = vdf0 / np.float(n_proc)


### HEATING VS W_PERP (beta = 1/9)
#
# -> reading simulation data, time averaging, and cooling corrections
# -> also: reading spectra of fluctuations, reducing to k_perp spectra, and time averaging
#
print "\n ### HEATING VS (W_PARA,W_PERP) ###"
#
for ind in range(it0,it1+1):
  if verb_diag:
    print "\n"
    print "#########################################################"
    print "### v-space analysis: distribution function & heating ###"
    print "#########################################################"
  print "\n time_index, time -> ",ind,", ",time[ind]
  #
  #reading files (the boolean variable decides if you need to also create and return v-spae axis: you do it only once per cycle) 
  vdf_, vprp, vprl = pegr.readnpy_vdf(path_read,ind,Nvperp,Nvpara,vperp_min,vperp_max,vpara_min,vpara_max,verbose=verb_read)
  edotv_prl_ = pegr.readnpy_vspaceheat_prl(path_read,ind,Nvperp,Nvpara,vperp_min,vperp_max,vpara_min,vpara_max,grid=False,verbose=verb_read)
  edotv_prp_ = pegr.readnpy_vspaceheat_prp(path_read,ind,Nvperp,Nvpara,vperp_min,vperp_max,vpara_min,vpara_max,grid=False,verbose=verb_read)
  #
  dvprp = vprp[2]-vprp[1]
  dvprl = vprl[2]-vprl[1]
  #
  #first normalization by number of processors
  vdf_ = vdf_ / np.float(n_proc)
  edotv_prl_ = edotv_prl_ / np.float(n_proc)
  edotv_prp_ = edotv_prp_ / np.float(n_proc)

  if apply_smoothing:
    ggsmooth = gaussian_filter(edotv_prp_,sigma=sigma_smoothing)
    edotv_prp_ = ggsmooth
    ggsmooth = gaussian_filter(edotv_prl_,sigma=sigma_smoothing)
    edotv_prl_ = ggsmooth

  
  #vdf output is actually vperp*f: restoring f
  vdf = np.zeros([Nvperp,Nvpara]) 
  edotv_prl = edotv_prl_
  edotv_prp = edotv_prp_
  for ivprp in range(Nvperp):
    vdf[ivprp,:] = vdf_[ivprp,:] / vprp[ivprp]
    vdf0[ivprp,:] = vdf0[ivprp,:] / vprp0[ivprp]

  Qprp = edotv_prp/(np.abs( np.abs(np.sum(edotv_prl*dvprp*dvprl)) + np.abs(np.sum(edotv_prp*dvprp*dvprl)) ))
  Qprl = edotv_prl/(np.abs( np.abs(np.sum(edotv_prl*dvprp*dvprl)) + np.abs(np.sum(edotv_prp*dvprp*dvprl)) ))

  if (cooling_corr_perp or cooling_corr_para):
    #correcting for numerical cooling
    print "\n [ apply cooling correction ]"
    for iit in range(it0corr,np.min([ind,it1corr])+1):
      #
      nnt = np.float(np.min([ind,it1corr])+1-it0corr)
      #
      #reading files (the boolean variable decides if you need to also create and return v-spae axis: you do it only once per cycle) 
      edotv_prl_ = pegr.readnpy_vspaceheat_prl(path_read,iit,Nvperp,Nvpara,vperp_min,vperp_max,vpara_min,vpara_max,grid=False,verbose=verb_read)
      edotv_prp_ = pegr.readnpy_vspaceheat_prp(path_read,iit,Nvperp,Nvpara,vperp_min,vperp_max,vpara_min,vpara_max,grid=False,verbose=verb_read)
      #
      #first normalization by number of processors
      edotv_prl_ /= np.float(n_proc)
      edotv_prp_ /= np.float(n_proc)
  
      if (iit == it0corr):
        if verb_diag:
          print "\n  [initializing arrays for average]"
        edotv_prl_corr = np.zeros([Nvperp,Nvpara])
        edotv_prp_corr = np.zeros([Nvperp,Nvpara])
  
      if apply_smoothing:
        ggsmooth = gaussian_filter(edotv_prp_,sigma=sigma_smoothing)
        edotv_prp_ = ggsmooth
        ggsmooth = gaussian_filter(edotv_prl_,sigma=sigma_smoothing)
        edotv_prl_ = ggsmooth
    
      #print " COOLING ? integral = ",np.sum(edotv_prl_*dvprp*dvprl)
      edotv_prl_corr += edotv_prl_ / nnt 
      edotv_prp_corr += edotv_prp_ / nnt 


    if cooling_corr_perp:
      print "  -> applying cooling corrections to Qperp "
      Qprp -= edotv_prp_corr/(np.abs( np.abs(np.sum(edotv_prl_corr*dvprp*dvprl)) + np.abs(np.sum(edotv_prp_corr*dvprp*dvprl)) ))
    else:
      print "  ** NO cooling corrections to Qperp ** "
  
    if cooling_corr_para:
      print "  -> applying cooling corrections to Qpara "
      Qprl -= edotv_prl_corr/(np.abs( np.abs(np.sum(edotv_prl_corr*dvprp*dvprl)) + np.abs(np.sum(edotv_prp_corr*dvprp*dvprl)) ))
    else:
      print "  ** NO cooling corrections to Qpara ** "


  #normalize Q to Qtot 
  Qtot = np.abs( np.sum(Qprp*dvprp*dvprl) + np.sum(Qprl*dvprp*dvprl) )
  Qprp /= Qtot
  Qprl /= Qtot
  print Qtot
  print " Qperp_tot/Q_tot = ",np.sum(Qprp*dvprp*dvprl)
  print " Qpara_tot/Q_tot = ",np.sum(Qprl*dvprp*dvprl)


  ### PLOTS ###

  #--lines and fonts
  line_thick = 1.25
  line_thick_aux = 0.75
  font_size = 13#9
  nlev = 128
  clrmap = 'seismic' #'bwr' #cmap
  
  #--set ranges
  xr_min_wprp = 0.
  xr_max_wprp = np.max(vprp)
  xr_min_wprl = np.min(vprl)
  xr_max_wprl = np.max(vprl)
  #min_Q = np.min([np.min(Qprl),np.min(Qprp)]) 
  #max_Q = np.max([np.max(Qprl),np.max(Qprp)])
  zmin_Qprl = -np.max([np.max(np.abs(Qprl)),1e-2])
  zmax_Qprl = np.max([np.max(np.abs(Qprl)),1e-2])
  zmin_Qprp = -np.max([np.max(np.abs(Qprp)),1e-2])
  zmax_Qprp = np.max([np.max(np.abs(Qprp)),1e-2])


  #--set figure real width
  width = width_2columns
  #
  fig1 = plt.figure(figsize=(3,3))
  fig1.set_figheight((np.sqrt(5.0)-1.0)/2.0 * width*0.55)
  fig1.set_figwidth(width*1.02)
  grid = plt.GridSpec(2, 9, hspace=0.0, wspace=0.0)
  #
  # Q_para 
  ax1a = fig1.add_subplot(grid[0:2,0:4])
  ax1a.contour(vprl,vprp,Qprl,nlev,vmin=zmin_Qprl,vmax=zmax_Qprl,cmap=clrmap)
  ax1a.axvline(x=1.0,c='k',linestyle=':',linewidth=line_thick_aux,alpha=0.66)
  ax1a.axvline(x=-1.0,c='k',linestyle=':',linewidth=line_thick_aux,alpha=0.66)
  ax1a.axvline(x=vA01,c='k',linestyle='--',linewidth=line_thick_aux,alpha=0.66)
  ax1a.axvline(x=-vA01,c='k',linestyle='--',linewidth=line_thick_aux,alpha=0.66)
  ax1a.axhline(y=1.0,c='k',linestyle=':',linewidth=line_thick_aux,alpha=0.66)
  ax1a.axhline(y=vA01,c='k',linestyle='--',linewidth=line_thick_aux,alpha=0.66)
  ax1a.set_xlim(xr_min_wprl,xr_max_wprl)
  ax1a.set_ylim(xr_min_wprp,xr_max_wprp)
  ax1a.set_xlabel(r'$w_\parallel/v_\mathrm{th,i0}$',fontsize=font_size)
  ax1a.set_ylabel(r'$w_\perp/v_\mathrm{th,i0}$',fontsize=font_size)
  ax1a.set_title(r'$Q_\mathrm{tot}^{-1}\langle Q_\parallel\rangle$',fontsize=font_size+1)
  ax1a.tick_params(labelsize=font_size)
  lbls_wprpvth = [r'$0$','',r'$1$','',r'$2$','',r'$3$','',r'$4$']
  ax1a.set_yticklabels(lbls_wprpvth)
  ax1a.text(-3.5,3.7,r'(a)',va='center',ha='center',color='k',rotation=0,fontsize=font_size+1,weight='bold')
  m1 = plt.cm.ScalarMappable(cmap=clrmap)
  m1.set_array(Qprl)
  m1.set_clim(zmin_Qprl, zmax_Qprl)
  cbar1 = fig1.colorbar(m1, boundaries=np.linspace(zmin_Qprl,zmax_Qprl,nlev+1),format='%0.2f',ticks=np.linspace(zmin_Qprl,zmax_Qprl,7))
  ax2a = ax1a.twiny()
  ax2a.set_xlim(xr_min_wprl,xr_max_wprl)
  ax2a.tick_params(labelsize=font_size)
  lbls_wprlvA01 = ['',r'$-v_\mathrm{A}$','','','','','',r'$v_\mathrm{A}$','']
  ax2a.set_xticklabels(lbls_wprlvA01)
  #
  # Q_perp
  ax1b = fig1.add_subplot(grid[0:2,5:9])
  ax1b.contour(vprl,vprp,Qprp,nlev,vmin=zmin_Qprp,vmax=zmax_Qprp,cmap=clrmap)
  ax1b.axvline(x=1.0,c='k',linestyle=':',linewidth=line_thick_aux,alpha=0.66)
  ax1b.axvline(x=-1.0,c='k',linestyle=':',linewidth=line_thick_aux,alpha=0.66)
  ax1b.axvline(x=vA01,c='k',linestyle='--',linewidth=line_thick_aux,alpha=0.66)
  ax1b.axvline(x=-vA01,c='k',linestyle='--',linewidth=line_thick_aux,alpha=0.66)
  ax1b.axhline(y=1.0,c='k',linestyle=':',linewidth=line_thick_aux,alpha=0.66)
  ax1b.axhline(y=vA01,c='k',linestyle='--',linewidth=line_thick_aux,alpha=0.66)
  ax1b.set_xlim(xr_min_wprl,xr_max_wprl)
  ax1b.set_ylim(xr_min_wprp,xr_max_wprp)
  ax1b.set_xlabel(r'$w_\parallel/v_\mathrm{th,i0}$',fontsize=font_size)
  ax1b.set_ylabel(r'$w_\perp/v_\mathrm{th,i0}$',fontsize=font_size)
  ax1b.set_title(r'$Q_\mathrm{tot}^{-1}\langle Q_\perp\rangle$',fontsize=font_size+1)
  ax1b.tick_params(labelsize=font_size)
  lbls_wprpvth = [r'$0$','',r'$1$','',r'$2$','',r'$3$','',r'$4$']
  ax1b.set_yticklabels(lbls_wprpvth)
  ax1b.text(-3.5,3.7,r'(b)',va='center',ha='center',color='k',rotation=0,fontsize=font_size+1,weight='bold')
  m2 = plt.cm.ScalarMappable(cmap=clrmap)
  m2.set_array(Qprp)
  m2.set_clim(zmin_Qprp, zmax_Qprp)
  cbar2 = plt.colorbar(m2, boundaries=np.linspace(zmin_Qprp,zmax_Qprp,nlev+1),format='%0.2f',ticks=np.linspace(zmin_Qprp,zmax_Qprp,7))
  ax2b = ax1b.twiny()
  ax2b.set_xlim(xr_min_wprl,xr_max_wprl)
  ax2b.tick_params(labelsize=font_size)
  lbls_wprlvA01 = ['',r'$-v_\mathrm{A}$','','','','','',r'$v_\mathrm{A}$','']
  ax2b.set_xticklabels(lbls_wprlvA01)
  #
  #--show and/or save
  if output_figure:
    plt.tight_layout()
    if (cooling_corr_perp and cooling_corr_para):
      flnm = "QperpQpara_2D_CoolCorrParaAndPerp"
    else:
      if (cooling_corr_perp):
        flnm = "QperpQpara_2D_CoolCorrPerp"
      else:
        if (cooling_corr_para):
          flnm = "QperpQpara_2D_CoolCorrPara"
        else:
          flnm = "QperpQpara_2D_NoCoolingCorrection"
    if apply_smoothing:
      flnm += '_smooth'
    flnm += '_large'
    flnm += '.'+'%05d'%ind
    path_output = path_save+flnm+fig_frmt
    plt.savefig(path_output,bbox_to_inches='tight')#,pad_inches=-1)
    plt.close()
    print " -> figure saved in:",path_output
  else:
   plt.show()




  Qprp_wprp = np.sum(Qprp*dvprl,axis=1)
  Qprp_wprl = np.sum(Qprp*dvprp,axis=0)
  Qprl_wprp = np.sum(Qprl*dvprl,axis=1)
  Qprl_wprl = np.sum(Qprl*dvprp,axis=0)
  
  
  #--set figure real width
  width = width_2columns
  #
  fig1 = plt.figure(figsize=(3,3))
  fig1.set_figheight((np.sqrt(5.0)-1.0)/2.0 * width*0.55)
  fig1.set_figwidth(width*1.02)
  grid = plt.GridSpec(2, 9, hspace=0.0, wspace=0.0)
  #
  # Q vs w_para 
  ax1a = fig1.add_subplot(grid[0:2,0:4])
  ax1a.plot(vprl,Qprl_wprl,color='darkorange',linewidth=line_thick,label=r'$Q_\parallel$')
  ax1a.plot(vprl,Qprp_wprl,color='darkmagenta',linewidth=line_thick,label=r'$Q_\perp$')
  ax1a.axvline(x=1.0,c='k',linestyle=':',linewidth=line_thick_aux,alpha=0.66)
  ax1a.axvline(x=-1.0,c='k',linestyle=':',linewidth=line_thick_aux,alpha=0.66)
  ax1a.axvline(x=vA01,c='k',linestyle='--',linewidth=line_thick_aux,alpha=0.66)
  ax1a.axvline(x=-vA01,c='k',linestyle='--',linewidth=line_thick_aux,alpha=0.66)
  ax1a.axhline(y=0.,c='k',linestyle=':',linewidth=line_thick_aux,alpha=0.66)
  ax1a.set_xlim(xr_min_wprl,xr_max_wprl)
  ax1a.set_ylim(np.min([np.min(Qprl_wprl),np.min(Qprp_wprl)]),np.max([np.max(Qprl_wprl),np.max(Qprp_wprl)]))
  ax1a.set_xlabel(r'$w_\parallel/v_\mathrm{th,i0}$',fontsize=font_size)
  ax1a.set_ylabel(r'$Q_\mathrm{tot}^{-1}\,\langle\mathrm{d}Q/\mathrm{d}w_\parallel\rangle$',fontsize=font_size)
  ax1a.tick_params(labelsize=font_size)
  ax1a.legend(loc='upper left',fontsize=font_size)
  ax2a = ax1a.twiny()
  ax2a.set_xlim(xr_min_wprl,xr_max_wprl)
  lbls_wprlvA01 = ['',r'$-v_\mathrm{A}$','','','','','',r'$v_\mathrm{A}$','']
  ax2a.set_xticklabels(lbls_wprlvA01)
  #
  # Q vs w_perp
  ax1b = fig1.add_subplot(grid[0:2,5:9])
  ax1b.plot(vprp,Qprl_wprp,color='darkorange',linewidth=line_thick,label=r'$Q_\parallel$')
  ax1b.plot(vprp,Qprp_wprp,color='darkmagenta',linewidth=line_thick,label=r'$Q_\perp$')
  ax1b.axvline(x=1.0,c='k',linestyle=':',linewidth=line_thick_aux,alpha=0.66)
  ax1b.axvline(x=vA01,c='k',linestyle='--',linewidth=line_thick_aux,alpha=0.66)
  ax1b.set_xlim(xr_min_wprp,xr_max_wprp)
  ax1b.set_ylim(np.min([np.min(Qprl_wprp),np.min(Qprp_wprp)]),np.max([np.max(Qprl_wprp),np.max(Qprp_wprp)]))
  ax1b.set_xlabel(r'$w_\perp/v_\mathrm{th,i0}$',fontsize=font_size)
  ax1b.set_ylabel(r'$Q_\mathrm{tot}^{-1}\,\langle\mathrm{d}Q/\mathrm{d}w_\perp\rangle$',fontsize=font_size)
  ax1b.axhline(y=0.,c='k',linestyle=':',linewidth=line_thick_aux,alpha=0.66)
  ax1b.tick_params(labelsize=font_size)
  ax1b.legend(loc='upper right',fontsize=font_size)
  ax2b = ax1b.twiny()
  ax2b.set_xlim(xr_min_wprp,xr_max_wprp)
  lbls_wprpvA01 = ['','','','','','',r'$v_\mathrm{A}$','','']
  ax2b.set_xticklabels(lbls_wprpvA01)
  #
  #--show and/or save
  if output_figure:
    plt.tight_layout()
    if (cooling_corr_perp and cooling_corr_para):
      flnm = "QperpQpara_1D_CoolCorrParaAndPerp"
    else:
      if (cooling_corr_perp):
        flnm = "QperpQpara_1D_CoolCorrPerp"
      else:
        if (cooling_corr_para):
          flnm = "QperpQpara_1D_CoolCorrPara"
        else:
          flnm = "QperpQpara_1D_NoCoolingCorrection"
    if apply_smoothing:
      flnm = flnm+'_smooth'
    flnm += '_large'
    flnm += '.'+'%05d'%ind
    path_output = path_save+flnm+fig_frmt
    plt.savefig(path_output,bbox_to_inches='tight')#,pad_inches=-1)
    plt.close()
    print " -> figure saved in:",path_output
  else:
   plt.show()
  


#

###

#####

#######

#####

###

#

###

#####

#######

#####

###

#

###

#####

#######

exit() #<><><><><><><><><><><>#

#######

#####

###

#

















