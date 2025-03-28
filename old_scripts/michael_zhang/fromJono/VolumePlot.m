function VolumePlot(data,x,y,z,zslice)
% Render the 3-D data on a slice plane at 45 degrees
    delete(gca) 

    if nargin<=4
        zslice = 1;
    end

% Initialization steps - only perform if they haven't been already
NX=length(x);LX=x(end)-x(1)+(x(2)-x(1));
NY=length(y);LY=y(end)-y(1)+(y(2)-y(1));
NZ=length(z);LZ=z(end)-z(1)+(z(2)-z(1));

data=double(permute(data,[2,1,3]));
%Grid
[XG,YG,ZG]=meshgrid(...
    linspace(0,LX,NX),linspace(0,LY,NY),linspace(0,LZ,NZ));
% Create a 45 degree slice
hslice = surf(...
    linspace(-0.4*sqrt(LX^2+LZ^2)+LX/2,0.4*sqrt(LX^2+LZ^2)+LX/2),...
    linspace(0,LY),...
    LZ/2*ones(100));
rotate(hslice,[0,1,0],atand(LZ/LX))
xd = get(hslice,'XData');
yd = get(hslice,'YData');
zd = get(hslice,'ZData');
delete(hslice)

% Draw main slice
% hS = slice(XG,YG,ZG,data,xd,yd,zd);
% set(hS,'FaceColor','interp',...
% 	'EdgeColor','none',...
% 	'DiffuseStrength',.8)
% Background faces
rngz = 1:ceil(NZ*zslice);

hold on
hx = slice(XG(:,:,rngz),YG(:,:,rngz),ZG(:,:,rngz),data(:,:,rngz),LX,[],[]);
set(hx,'FaceColor','interp','EdgeColor','none','DiffuseStrength',.8)
hx2 = slice(XG,YG,ZG,data,0,[],[]);
set(hx2,'FaceColor','interp','EdgeColor','none')

hy = slice(XG(:,:,rngz),YG(:,:,rngz),ZG(:,:,rngz),data(:,:,rngz),[],0,[]);
set(hy,'FaceColor','interp','EdgeColor','none')

hy2 = slice(XG,YG,ZG,data,[],LY,[]);
set(hy2,'FaceColor','interp','EdgeColor','none')

hz = slice(XG,YG,ZG,data,[],[],LZ*zslice);
set(hz,'FaceColor','interp','EdgeColor','none')

% Make it look better
daspect([1,1,1])
axis tight
box on
view(70,16)
camproj perspective
lightangle(45,45)
set(gcf,'Renderer','zbuffer')
% xlabel('x')
% ylabel('y')
% zlabel('z')
% caxis([-3.5 3.5])
colorbar
% drawnow

end