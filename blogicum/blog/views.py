from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView
)

from django.core.paginator import Paginator

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin

from django.urls import reverse

from django.shortcuts import redirect, render, get_object_or_404

from blog.models import Post, Category, Comment
from blog.forms import PostForm, CommentForm, CategoryForm, UserUpdateForm

User = get_user_model()


class PostListView(ListView):
    '''показывать все посты.'''
    model = Post
    ordering = '-pub_date'
    paginate_by = 10
    template_name = 'blog/index.html'


class PostCreateView(LoginRequiredMixin, CreateView):
    '''создание поста'''
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'profile_slug': self.object.author})  # type: ignore

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.comment_count = 0
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UpdateView):
    '''редактирование поста'''
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['pk'])
        if instance.author != request.user:
            return redirect('blog:post_detail',
                            self.get_object().pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'pk': self.object.pk})  # type: ignore


class PostDeleteView(LoginRequiredMixin, DeleteView):
    '''удаление поста'''
    model = Post
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['pk'])
        if instance.author != request.user:
            return redirect('blog:post_detail',
                            self.get_object().pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:profile',
                       args=[self.request.user.username])  # type: ignore


class PostDetailView(DetailView):
    '''просмотр отдельного поста'''
    model = Post
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author')  # type: ignore
        )
        return context


class CategoryDetailView(DetailView):
    '''просмотр отдельно категории'''
    model = Category
    template_name = 'blog/category.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = Post.objects.filter(category__slug=self.object.slug).order_by('-pub_date')
        paginator = Paginator(posts, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        return context


def profile(request, profile_slug):
    '''просмотр профиля пользователя'''
    template = 'blog/profile.html'
    profile = get_object_or_404(
        User,
        username=profile_slug,
    )
    posts = Post.objects.published(  # type: ignore
        author__username=profile_slug
        ).order_by('-pub_date')
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'profile': profile,
        'page_obj': page_obj
    }
    return render(request, template, context)


class UserUpdateView(LoginRequiredMixin, UpdateView):
    '''редактирование профиля пользователя'''
    model = User
    template_name = 'blog/user.html'
    form_class = UserUpdateForm

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile',
                       args=[self.request.user.username])  # type: ignore


class CommentCreateView(LoginRequiredMixin, CreateView):
    '''создание комментария'''
    object = None
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post_id = self.kwargs['pk']
        form.instance.object = self.object
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'pk': self.object.post_id})  # type: ignore


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    '''обновление комментария'''
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'pk': self.object.post_id})  # type: ignore


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    '''Удаление комментария.'''
    model = Comment
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'pk': self.get_object().post_id})  # type: ignore
