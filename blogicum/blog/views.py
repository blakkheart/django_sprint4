from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from django.conf import settings
from blog.forms import CommentForm, PostForm, UserUpdateForm
from blog.models import Category, Comment, Post


User = get_user_model()


class PostUpdateDeleteMixin:
    """
    Mixin for update and delete comment class.
    Override dispatch method.
    """
    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['pk'])
        if instance.author != request.user:
            return redirect('blog:post_detail',
                            self.get_object().pk)  # type: ignore
        return super().dispatch(request, *args, **kwargs)  # type: ignore


class CommentUpdateDeleteMixin:
    """
    Mixin for update and delete comment class.
    Override dispatch and get_success_url methods.
    """
    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=kwargs['pk'])
        if instance.author != request.user:
            return redirect('blog:post_detail',
                            self.get_object().pk)  # type: ignore
        return super().dispatch(request, *args, **kwargs)  # type: ignore

    def get_success_url(self):
        return reverse('blog:post_detail',
                       args=(self.get_object().post_id,))  # type: ignore


class PostListView(ListView):
    '''Show all posts.'''
    model = Post
    queryset = Post.objects.filter(
        is_published=True,
        pub_date__lt=timezone.now(),
        category__is_published=True
    ).annotate(comment_count=Count('comments'))
    ordering = '-pub_date'
    paginate_by = settings.PAGINATE_BY
    template_name = 'blog/index.html'


class PostCreateView(LoginRequiredMixin, CreateView):
    '''Create post.'''
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile',
                       args=(self.object.author,))  # type: ignore


class PostDetailView(DetailView):
    '''Show selected post.'''
    model = Post
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author')  # type: ignore
        )
        return context


class PostUpdateView(LoginRequiredMixin, PostUpdateDeleteMixin, UpdateView):
    '''Edit selected post.'''
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse('blog:post_detail',
                       args=(self.object.pk,))  # type: ignore


class PostDeleteView(LoginRequiredMixin, PostUpdateDeleteMixin, DeleteView):
    '''Delete selected post.'''
    model = Post
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse('blog:profile',
                       args=(self.request.user.username,))  # type: ignore


class CategoryDetailView(ListView):
    '''Show selected category info and posts.'''
    model = Post
    template_name = 'blog/category.html'
    paginate_by = settings.PAGINATE_BY
    ordering = '-pub_date'

    def get_queryset(self):
        get_object_or_404(
            Category,
            slug=self.kwargs['slug'],
            is_published=True
        )
        return super().get_queryset().filter(
            is_published=True,
            pub_date__lt=timezone.now(),
            category__slug=self.kwargs['slug']
        ).annotate(comment_count=Count('comments'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = Category.objects.get(
            slug=self.kwargs['slug'])
        context['category'] = category
        return context


class UserListView(ListView):
    '''Show selected profile info and posts.'''
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = settings.PAGINATE_BY
    ordering = '-pub_date'

    def get_queryset(self):
        if self.request.user.username == self.kwargs['slug']:  # type: ignore
            return super().get_queryset().filter(
                author__username=self.kwargs['slug']
            ).annotate(comment_count=Count('comments'))
        return super().get_queryset().filter(
            is_published=True,
            pub_date__lt=timezone.now(),
            author__username=self.kwargs['slug']
        ).annotate(comment_count=Count('comments'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_object_or_404(User, username=self.kwargs['slug'])
        context['profile'] = profile
        return context


class UserUpdateView(LoginRequiredMixin, UpdateView):
    '''Edit user's profile.'''
    model = User
    template_name = 'blog/user.html'
    form_class = UserUpdateForm

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile',
                       args=(self.request.user.username,))  # type: ignore


class CommentCreateView(LoginRequiredMixin, CreateView):
    '''Create comment to selected post.'''
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
                       args=(self.object.post_id,))  # type: ignore


class CommentUpdateView(LoginRequiredMixin,
                        CommentUpdateDeleteMixin, UpdateView):
    '''Update selected comment.'''
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'


class CommentDeleteView(LoginRequiredMixin,
                        CommentUpdateDeleteMixin, DeleteView):
    '''Delete selected comment.'''
    model = Comment
    template_name = 'blog/comment.html'
