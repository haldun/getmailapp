require 'sinatra'

post '/hi' do
  puts request.body
end
