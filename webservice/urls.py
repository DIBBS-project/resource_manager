from django.conf.urls import patterns, include, url
from django.contrib import admin
from  webservice import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'webservice.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^index/',  views.index, name='index'),
    url(r'^$',  views.index, name='index'),

    # Users
    url(r'^register_new_user/?$', views.register_new_user),
    url(r'^generate_new_token/?$', views.generate_new_token),

    # FS Files
    url(r'^fs/ls/(?P<path>[0-9a-zA-Z/_.-]+)/$', views.fs_file_detail),
    url(r'^fs/ls//$', views.fs_file_detail),
    url(r'^fs/run/(?P<path>[0-9a-zA-Z/_.-]+)/$', views.run_file),
    url(r'^fs/mkdir/(?P<path>[0-9a-zA-Z/_.-]+)/$', views.create_fs_folder),
    url(r'^fs/rm/(?P<path>[0-9a-zA-Z/_.-]+)/$', views.fs_delete_file),
    url(r'^fs/rmdir/(?P<path>[0-9a-zA-Z/_.-]+)/$', views.fs_delete_folder),
    url(r'^fs/upload/(?P<path>[0-9a-zA-Z/_.-]+)/$', views.upload_fs_file),
    url(r'^fs/download/(?P<path>[0-9a-zA-Z/_.-]+)/$', views.download_fs_file),

    # HDFS Files
    url(r'^hdfs/ls/(?P<path>[0-9a-zA-Z/_.-]+)/$', views.hdfs_file_detail),
    url(r'^hdfs/ls//$', views.hdfs_file_detail),
    url(r'^hdfs/mkdir/(?P<path>[0-9a-zA-Z/_.-]+)/$', views.create_hdfs_folder),
    url(r'^hdfs/rm/(?P<path>[0-9a-zA-Z/_.-]+)/$', views.hdfs_delete_file),
    url(r'^hdfs/rmdir/(?P<path>[0-9a-zA-Z/_.-]+)/$', views.hdfs_delete_folder),
    url(r'^hdfs/upload/(?P<hdfspath>[0-9a-zA-Z/_.-]+)/$', views.upload_hdfs_file),
    url(r'^hdfs/download/(?P<hdfspath>[0-9a-zA-Z/_.-]+)/$', views.download_hdfs_file),
    url(r'^hdfs/copytolocal/(?P<hdfspath>[0-9a-zA-Z/_.-]+)/_/(?P<localpath>[0-9a-zA-Z/_.-]+)/$', views.hdfs_copy_to_local),
    url(r'^hdfs/mergedir/(?P<hdfspath>[0-9a-zA-Z/_.-]+)/_/(?P<localpath>[0-9a-zA-Z/_.-]+)/$', views.hdfs_merge_directory),

    # Jobs
    url(r'^jobs/?$', views.job_list),
    url(r'^jobs/(?P<pk>[0-9]+)/$', views.job_detail),
    url(r'^run_hadoop_job/(?P<pk>[0-9]+)/$', views.run_hadoop_job),
    url(r'^get_running_jobs/$', views.get_running_jobs),
)
