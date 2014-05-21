def getPage(request, name='page'):
    if request.GET.has_key(name) and len(request.GET[name]) > 0:
        return int(request.GET[name])
    else:
        return 0

class Pagination:
    def __init__(self, request, count, numPerPage, pageParam='page'):
        count = int(count)
        self.page = getPage(request, pageParam)
        self.pageParam = pageParam
        self.count = count
        self.numPerPage = numPerPage
        self.first = self.page * numPerPage
        self.last = self.first + numPerPage
        if self.page > 0:
            self.prev = self.page -1 
            self.hasPrev = True
        else:
            self.prev = None
            self.hasPrev = False
        if self.last < count:
            self.next = self.page + 1
            self.hasNext = True
        else:
            self.next = None
            self.hasNext = False
        self.totalPages = count / numPerPage
        if count % numPerPage != 0:
             self.totalPages += 1
        self.manyPages = self.totalPages > 1
    def slice(self, list):
        return list[self.first:self.last]
    def url(self):
        return self.pageParam + '=' + str(self.page)
    def urlNext(self):
        return self.pageParam + '=' + str(self.page + 1)
    def urlPrev(self):
        return self.pageParam + '=' + str(self.page - 1)
        
