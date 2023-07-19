d:
	hexo clean && hexo deploy -g

s:
	hexo clean && hexo server

mv2draft:
	mv source/_posts/$(POST) source/_drafts/