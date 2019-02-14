def get_page(request, name='page'):
    if name in request.GET and len(request.GET[name]) > 0:
        return int(request.GET[name])
    else:
        return 0


class Pagination:
    def __init__(self, request, count, num_per_page, page_param='page'):
        count = int(count)
        self.page = get_page(request, page_param)
        self.page_param = page_param
        self.count = count
        self.num_per_page = num_per_page
        self.first = self.page * num_per_page
        self.last = self.first + num_per_page
        if self.page > 0:
            self.prev = self.page - 1
            self.has_prev = True
        else:
            self.prev = None
            self.has_prev = False
        if self.last < count:
            self.next = self.page + 1
            self.has_next = True
        else:
            self.next = None
            self.has_next = False
        self.total_pages = count / num_per_page
        if count % num_per_page != 0:
            self.total_pages += 1
        self.many_pages = self.total_pages > 1

    def slice(self, the_list):
        return the_list[self.first:self.last]

    def url(self):
        return self.page_param + '=' + str(self.page)

    def url_next(self):
        return self.page_param + '=' + str(self.page + 1)

    def url_prev(self):
        return self.page_param + '=' + str(self.page - 1)
